"""
microdot
--------

The ``microdot`` module defines a few classes that help implement HTTP-based
servers for MicroPython and standard Python, with multithreading support for
Python interpreters that support it.
"""
try:
    from sys import print_exception
except ImportError:  # pragma: no cover
    import traceback

    def print_exception(exc):
        traceback.print_exc()
try:
    import uerrno as errno
except ImportError:
    import errno

concurrency_mode = 'threaded'

try:  # pragma: no cover
    import threading

    def create_thread(f, *args, **kwargs):
        # use the threading module
        threading.Thread(target=f, args=args, kwargs=kwargs).start()
except ImportError:  # pragma: no cover
    try:
        import _thread

        def create_thread(f, *args, **kwargs):
            # use MicroPython's _thread module
            def run():
                f(*args, **kwargs)

            _thread.start_new_thread(run, ())
    except ImportError:
        def create_thread(f, *args, **kwargs):
            # no threads available, call function synchronously
            f(*args, **kwargs)

        concurrency_mode = 'sync'
try:
    import ujson as json
except ImportError:
    import json

try:
    import ure as re
except ImportError:
    import re

try:
    import usocket as socket
except ImportError:
    try:
        import socket
    except ImportError:  # pragma: no cover
        socket = None

from request import Request
from response import Response

def urldecode(string):
    string = string.replace('+', ' ')
    parts = string.split('%')
    if len(parts) == 1:
        return string
    result = [parts[0]]
    for item in parts[1:]:
        if item == '':
            result.append('%')
        else:
            code = item[:2]
            result.append(chr(int(code, 16)))
            result.append(item[2:])
    return ''.join(result)


class URLPattern():
    def __init__(self, url_pattern):
        self.pattern = ''
        self.args = []
        use_regex = False
        for segment in url_pattern.lstrip('/').split('/'):
            if segment and segment[0] == '<':
                if segment[-1] != '>':
                    raise ValueError('invalid URL pattern')
                segment = segment[1:-1]
                if ':' in segment:
                    type_, name = segment.rsplit(':', 1)
                else:
                    type_ = 'string'
                    name = segment
                if type_ == 'string':
                    pattern = '[^/]+'
                elif type_ == 'int':
                    pattern = '\\d+'
                elif type_ == 'path':
                    pattern = '.+'
                elif type_.startswith('re:'):
                    pattern = type_[3:]
                else:
                    raise ValueError('invalid URL segment type')
                use_regex = True
                self.pattern += '/({pattern})'.format(pattern=pattern)
                self.args.append({'type': type_, 'name': name})
            else:
                self.pattern += '/{segment}'.format(segment=segment)
        if use_regex:
            self.pattern = re.compile('^' + self.pattern + '$')

    def match(self, path):
        if isinstance(self.pattern, str):
            if path != self.pattern:
                return
            return {}
        g = self.pattern.match(path)
        if not g:
            return
        args = {}
        i = 1
        for arg in self.args:
            value = g.group(i)
            if arg['type'] == 'int':
                value = int(value)
            args[arg['name']] = value
            i += 1
        return args


class Microdot():
    """An HTTP application class.

    This class implements an HTTP application instance and is heavily
    influenced by the ``Flask`` class of the Flask framework. It is typically
    declared near the start of the main application script.

    Example::

        from microdot import Microdot

        app = Microdot()
    """

    def __init__(self):
        self.url_map = []
        self.before_request_handlers = []
        self.after_request_handlers = []
        self.error_handlers = {}
        self.shutdown_requested = False
        self.debug = False
        self.server = None

    def route(self, url_pattern, methods=None):
        """Decorator that is used to register a function as a request handler
        for a given URL.

        :param url_pattern: The URL pattern that will be compared against
                            incoming requests.
        :param methods: The list of HTTP methods to be handled by the
                        decorated function. If omitted, only ``GET`` requests
                        are handled.

        The URL pattern can be a static path (for example, ``/users`` or
        ``/api/invoices/search``) or a path with dynamic components enclosed
        in ``<`` and ``>`` (for example, ``/users/<id>`` or
        ``/invoices/<number>/products``). Dynamic path components can also
        include a type prefix, separated from the name with a colon (for
        example, ``/users/<int:id>``). The type can be ``string`` (the
        default), ``int``, ``path`` or ``re:[regular-expression]``.

        The first argument of the decorated function must be
        the request object. Any path arguments that are specified in the URL
        pattern are passed as keyword arguments. The return value of the
        function must be a :class:`Response` instance, or the arguments to
        be passed to this class.

        Example::

            @app.route('/')
            def index(request):
                return 'Hello, world!'
        """
        def decorated(f):
            self.url_map.append(
                (methods or ['GET'], URLPattern(url_pattern), f))
            return f
        return decorated

    def get(self, url_pattern):
        """Decorator that is used to register a function as a ``GET`` request
        handler for a given URL.

        :param url_pattern: The URL pattern that will be compared against
                            incoming requests.

        This decorator can be used as an alias to the ``route`` decorator with
        ``methods=['GET']``.

        Example::

            @app.get('/users/<int:id>')
            def get_user(request, id):
                # ...
        """
        return self.route(url_pattern, methods=['GET'])

    def post(self, url_pattern):
        """Decorator that is used to register a function as a ``POST`` request
        handler for a given URL.

        :param url_pattern: The URL pattern that will be compared against
                            incoming requests.

        This decorator can be used as an alias to the``route`` decorator with
        ``methods=['POST']``.

        Example::

            @app.post('/users')
            def create_user(request):
                # ...
        """
        return self.route(url_pattern, methods=['POST'])

    def put(self, url_pattern):
        """Decorator that is used to register a function as a ``PUT`` request
        handler for a given URL.

        :param url_pattern: The URL pattern that will be compared against
                            incoming requests.

        This decorator can be used as an alias to the ``route`` decorator with
        ``methods=['PUT']``.

        Example::

            @app.put('/users/<int:id>')
            def edit_user(request, id):
                # ...
        """
        return self.route(url_pattern, methods=['PUT'])

    def patch(self, url_pattern):
        """Decorator that is used to register a function as a ``PATCH`` request
        handler for a given URL.

        :param url_pattern: The URL pattern that will be compared against
                            incoming requests.

        This decorator can be used as an alias to the ``route`` decorator with
        ``methods=['PATCH']``.

        Example::

            @app.patch('/users/<int:id>')
            def edit_user(request, id):
                # ...
        """
        return self.route(url_pattern, methods=['PATCH'])

    def delete(self, url_pattern):
        """Decorator that is used to register a function as a ``DELETE``
        request handler for a given URL.

        :param url_pattern: The URL pattern that will be compared against
                            incoming requests.

        This decorator can be used as an alias to the ``route`` decorator with
        ``methods=['DELETE']``.

        Example::

            @app.delete('/users/<int:id>')
            def delete_user(request, id):
                # ...
        """
        return self.route(url_pattern, methods=['DELETE'])

    def before_request(self, f):
        """Decorator to register a function to run before each request is
        handled. The decorated function must take a single argument, the
        request object.

        Example::

            @app.before_request
            def func(request):
                # ...
        """
        self.before_request_handlers.append(f)
        return f

    def after_request(self, f):
        """Decorator to register a function to run after each request is
        handled. The decorated function must take two arguments, the request
        and response objects. The return value of the function must be an
        updated response object.

        Example::

            @app.before_request
            def func(request, response):
                # ...
        """
        self.after_request_handlers.append(f)
        return f

    def errorhandler(self, status_code_or_exception_class):
        """Decorator to register a function as an error handler. Error handler
        functions for numeric HTTP status codes must accept a single argument,
        the request object. Error handler functions for Python exceptions
        must accept two arguments, the request object and the exception
        object.

        :param status_code_or_exception_class: The numeric HTTP status code or
                                               Python exception class to
                                               handle.

        Examples::

            @app.errorhandler(404)
            def not_found(request):
                return 'Not found'

            @app.errorhandler(RuntimeError)
            def runtime_error(request, exception):
                return 'Runtime error'
        """
        def decorated(f):
            self.error_handlers[status_code_or_exception_class] = f
            return f
        return decorated

    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Start the web server. This function does not normally return, as
        the server enters an endless listening loop. The :func:`shutdown`
        function provides a method for terminating the server gracefully.

        :param host: The hostname or IP address of the network interface that
                     will be listening for requests. A value of ``'0.0.0.0'``
                     (the default) indicates that the server should listen for
                     requests on all the available interfaces, and a value of
                     ``127.0.0.1`` indicates that the server should listen
                     for requests only on the internal networking interface of
                     the host.
        :param port: The port number to listen for requests. The default is
                     port 5000.
        :param debug: If ``True``, the server logs debugging information. The
                      default is ``False``.

        Example::

            from microdot import Microdot

            app = Microdot()

            @app.route('/')
            def index():
                return 'Hello, world!'

            app.run(debug=True)
        """
        self.debug = debug
        self.shutdown_requested = False

        self.server = socket.socket()
        ai = socket.getaddrinfo(host, port)
        addr = ai[0][-1]

        if self.debug:  # pragma: no cover
            print('Starting {mode} server on {host}:{port}...'.format(
                mode=concurrency_mode, host=host, port=port))
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(addr)
        self.server.listen(5)

        while not self.shutdown_requested:
            try:
                sock, addr = self.server.accept()
            except OSError as exc:  # pragma: no cover
                if exc.errno == errno.ECONNABORTED:
                    break
                else:
                    raise
            create_thread(self.handle_request, sock, addr)

    def shutdown(self):
        """Request a server shutdown. The server will then exit its request
        listening loop and the :func:`run` function will return. This function
        can be safely called from a route handler, as it only schedules the
        server to terminate as soon as the request completes.

        Example::

            @app.route('/shutdown')
            def shutdown(request):
                request.app.shutdown()
                return 'The server is shutting down...'
        """
        self.shutdown_requested = True

    def find_route(self, req):
        f = None
        for route_methods, route_pattern, route_handler in self.url_map:
            if req.method in route_methods:
                req.url_args = route_pattern.match(req.path)
                if req.url_args is not None:
                    f = route_handler
                    break
        return f

    def handle_request(self, sock, addr):
        if not hasattr(sock, 'readline'):  # pragma: no cover
            stream = sock.makefile("rwb")
        else:
            stream = sock

        req = None
        try:
            req = Request.create(self, stream, addr)
        except Exception as exc:  # pragma: no cover
            print_exception(exc)
        res = self.dispatch_request(req)
        res.write(stream)
        try:
            stream.close()
        except OSError as exc:  # pragma: no cover
            if exc.errno == 32:  # errno.EPIPE
                pass
            else:
                raise
        if stream != sock:  # pragma: no cover
            sock.close()
        if self.shutdown_requested:  # pragma: no cover
            self.server.close()
        if self.debug and req:  # pragma: no cover
            print('{method} {path} {status_code}'.format(
                method=req.method, path=req.path,
                status_code=res.status_code))

    def dispatch_request(self, req):
        if req:
            if req.content_length > req.max_content_length:
                if 413 in self.error_handlers:
                    res = self.error_handlers[413](req)
                else:
                    res = 'Payload too large', 413
            else:
                f = self.find_route(req)
                try:
                    res = None
                    if f:
                        for handler in self.before_request_handlers:
                            res = handler(req)
                            if res:
                                break
                        if res is None:
                            res = f(req, **req.url_args)
                        if isinstance(res, tuple):
                            res = Response(*res)
                        elif not isinstance(res, Response):
                            res = Response(res)
                        for handler in self.after_request_handlers:
                            res = handler(req, res) or res
                    elif 404 in self.error_handlers:
                        res = self.error_handlers[404](req)
                    else:
                        res = 'Not found', 404
                except Exception as exc:
                    print_exception(exc)
                    res = None
                    if exc.__class__ in self.error_handlers:
                        try:
                            res = self.error_handlers[exc.__class__](req, exc)
                        except Exception as exc2:  # pragma: no cover
                            print_exception(exc2)
                    if res is None:
                        if 500 in self.error_handlers:
                            res = self.error_handlers[500](req)
                        else:
                            res = 'Internal server error', 500
        else:
            res = 'Bad request', 400
        if isinstance(res, tuple):
            res = Response(*res)
        elif not isinstance(res, Response):
            res = Response(res)
        return res


redirect = Response.redirect
send_file = Response.send_file

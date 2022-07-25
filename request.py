try:
    import ujson as json
except ImportError:
    import json


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

class Request():
    """An HTTP request class.

    :var app: The application instance to which this request belongs.
    :var client_addr: The address of the client, as a tuple (host, port).
    :var method: The HTTP method of the request.
    :var path: The path portion of the URL.
    :var query_string: The query string portion of the URL.
    :var args: The parsed query string, as a :class:`MultiDict` object.
    :var headers: A dictionary with the headers included in the request.
    :var cookies: A dictionary with the cookies included in the request.
    :var content_length: The parsed ``Content-Length`` header.
    :var content_type: The parsed ``Content-Type`` header.
    :var stream: The input stream, containing the request body.
    :var body: The body of the request, as bytes.
    :var json: The parsed JSON body, as a dictionary or list, or ``None`` if
               the request does not have a JSON body.
    :var form: The parsed form submission body, as a :class:`MultiDict` object,
               or ``None`` if the request does not have a form submission.
    :var g: A general purpose container for applications to store data during
            the life of the request.
    """
    #: Specify the maximum payload size that is accepted. Requests with larger
    #: payloads will be rejected with a 413 status code. Applications can
    #: change this maximum as necessary.
    #:
    #: Example::
    #:
    #:    Request.max_content_length = 1 * 1024 * 1024  # 1MB requests allowed
    max_content_length = 16 * 1024

    #: Specify the maximum payload size that can be stored in ``body``.
    #: Requests with payloads that are larger than this size and up to
    #: ``max_content_length`` bytes will be accepted, but the application will
    #: only be able to access the body of the request by reading from
    #: ``stream``. Set to 0 if you always access the body as a stream.
    #:
    #: Example::
    #:
    #:    Request.max_body_length = 4 * 1024  # up to 4KB bodies read
    max_body_length = 16 * 1024

    #: Specify the maximum length allowed for a line in the request. Requests
    #: with longer lines will not be correctly interpreted. Applications can
    #: change this maximum as necessary.
    #:
    #: Example::
    #:
    #:    Request.max_readline = 16 * 1024  # 16KB lines allowed
    max_readline = 2 * 1024

    class G:
        pass

    def __init__(self, app, client_addr, method, url, http_version, headers,
                 body=None, stream=None):
        self.app = app
        self.client_addr = client_addr
        self.method = method
        self.path = url
        self.http_version = http_version
        if '?' in self.path:
            self.path, self.query_string = self.path.split('?', 1)
            self.args = self._parse_urlencoded(self.query_string)
        else:
            self.query_string = None
            self.args = {}
        self.headers = headers
        self.cookies = {}
        self.content_length = 0
        self.content_type = None
        for header, value in self.headers.items():
            header = header.lower()
            if header == 'content-length':
                self.content_length = int(value)
            elif header == 'content-type':
                self.content_type = value
            elif header == 'cookie':
                for cookie in value.split(';'):
                    name, value = cookie.strip().split('=', 1)
                    self.cookies[name] = value
        self._body = body
        self.body_used = False
        self._stream = stream
        self.stream_used = False
        self._json = None
        self._form = None
        self.g = Request.G()

    @staticmethod
    def create(app, client_stream, client_addr):
        """Create a request object.

        :param app: The Microdot application instance.
        :param client_stream: An input stream from where the request data can
                              be read.
        :param client_addr: The address of the client, as a tuple.

        This method returns a newly created ``Request`` object.
        """
        # request line
        line = Request._safe_readline(client_stream).strip().decode()
        if not line:
            return None
        method, url, http_version = line.split()
        http_version = http_version.split('/', 1)[1]

        # headers
        headers = {}
        while True:
            line = Request._safe_readline(client_stream).strip().decode()
            if line == '':
                break
            header, value = line.split(':', 1)
            value = value.strip()
            headers[header] = value

        return Request(app, client_addr, method, url, http_version, headers,
                       stream=client_stream)

    def _parse_urlencoded(self, urlencoded):
        data = MultiDict()
        for k, v in [pair.split('=', 1) for pair in urlencoded.split('&')]:
            data[urldecode(k)] = urldecode(v)
        return data

    @property
    def body(self):
        if self.stream_used:
            raise RuntimeError('Cannot use both stream and body')
        if self._body is None:
            self._body = b''
            if self.content_length and \
                    self.content_length <= Request.max_body_length:
                while len(self._body) < self.content_length:
                    data = self._stream.read(
                        self.content_length - len(self._body))
                    if len(data) == 0:  # pragma: no cover
                        raise EOFError()
                    self._body += data
                self.body_used = True
        return self._body

    @property
    def stream(self):
        if self.body_used:
            raise RuntimeError('Cannot use both stream and body')
        self.stream_used = True
        return self._stream

    @property
    def json(self):
        if self._json is None:
            if self.content_type is None:
                return None
            mime_type = self.content_type.split(';')[0]
            if mime_type != 'application/json':
                return None
            self._json = json.loads(self.body.decode())
        return self._json

    @property
    def form(self):
        if self._form is None:
            if self.content_type is None:
                return None
            mime_type = self.content_type.split(';')[0]
            if mime_type != 'application/x-www-form-urlencoded':
                return None
            self._form = self._parse_urlencoded(self.body.decode())
        return self._form

    @staticmethod
    def _safe_readline(stream):
        line = stream.readline(Request.max_readline + 1)
        if len(line) > Request.max_readline:
            raise ValueError('line too long')
        return line

class MultiDict(dict):
    """A subclass of dictionary that can hold multiple values for the same
    key. It is used to hold key/value pairs decoded from query strings and
    form submissions.

    :param initial_dict: an initial dictionary of key/value pairs to
                         initialize this object with.

    Example::

        >>> d = MultiDict()
        >>> d['sort'] = 'name'
        >>> d['sort'] = 'email'
        >>> print(d['sort'])
        'name'
        >>> print(d.getlist('sort'))
        ['name', 'email']
    """
    def __init__(self, initial_dict=None):
        super().__init__()
        if initial_dict:
            for key, value in initial_dict.items():
                self[key] = value

    def __setitem__(self, key, value):
        if key not in self:
            super().__setitem__(key, [])
        super().__getitem__(key).append(value)

    def __getitem__(self, key):
        return super().__getitem__(key)[0]

    def get(self, key, default=None, type=None):
        """Return the value for a given key.

        :param key: The key to retrieve.
        :param default: A default value to use if the key does not exist.
        :param type: A type conversion callable to apply to the value.

        If the multidict contains more than one value for the requested key,
        this method returns the first value only.

        Example::

            >>> d = MultiDict()
            >>> d['age'] = '42'
            >>> d.get('age')
            '42'
            >>> d.get('age', type=int)
            42
            >>> d.get('name', default='noname')
            'noname'
        """
        if key not in self:
            return default
        value = self[key]
        if type is not None:
            value = type(value)
        return value

    def getlist(self, key, type=None):
        """Return all the values for a given key.

        :param key: The key to retrieve.
        :param type: A type conversion callable to apply to the values.

        If the requested key does not exist in the dictionary, this method
        returns an empty list.

        Example::

            >>> d = MultiDict()
            >>> d.getlist('items')
            []
            >>> d['items'] = '3'
            >>> d.getlist('items')
            ['3']
            >>> d['items'] = '56'
            >>> d.getlist('items')
            ['3', '56']
            >>> d.getlist('items', type=int)
            [3, 56]
        """
        if key not in self:
            return []
        values = super().__getitem__(key)
        if type is not None:
            values = [type(value) for value in values]
        return values

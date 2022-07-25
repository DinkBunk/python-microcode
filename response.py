class Response():
    """An HTTP response class.

    :param body: The body of the response. If a dictionary or list is given,
                 a JSON formatter is used to generate the body. If a file-like
                 object or a generator is given, a streaming response is used.
                 If a string is given, it is encoded from UTF-8. Else, the
                 body should be a byte sequence.
    :param status_code: The numeric HTTP status code of the response. The
                        default is 200.
    :param headers: A dictionary of headers to include in the response.
    :param reason: A custom reason phrase to add after the status code. The
                   default is "OK" for responses with a 200 status code and
                   "N/A" for any other status codes.
    """
    types_map = {
        'css': 'text/css',
        'gif': 'image/gif',
        'html': 'text/html',
        'jpg': 'image/jpeg',
        'js': 'application/javascript',
        'json': 'application/json',
        'png': 'image/png',
        'txt': 'text/plain',
    }
    send_file_buffer_size = 1024

    def __init__(self, body='', status_code=200, headers=None, reason=None):
        if body is None and status_code == 200:
            body = ''
            status_code = 204
        self.status_code = status_code
        self.headers = headers.copy() if headers else {}
        self.reason = reason
        if isinstance(body, (dict, list)):
            self.body = json.dumps(body).encode()
            self.headers['Content-Type'] = 'application/json'
        elif isinstance(body, str):
            self.body = body.encode()
        else:
            # this applies to bytes, file-like objects or generators
            self.body = body

    def set_cookie(self, cookie, value, path=None, domain=None, expires=None,
                   max_age=None, secure=False, http_only=False):
        """Add a cookie to the response.

        :param cookie: The cookie's name.
        :param value: The cookie's value.
        :param path: The cookie's path.
        :param domain: The cookie's domain.
        :param expires: The cookie expiration time, as a ``datetime`` object.
        :param max_age: The cookie's ``Max-Age`` value.
        :param secure: The cookie's ``secure`` flag.
        :param http_only: The cookie's ``HttpOnly`` flag.
        """
        http_cookie = '{cookie}={value}'.format(cookie=cookie, value=value)
        if path:
            http_cookie += '; Path=' + path
        if domain:
            http_cookie += '; Domain=' + domain
        if expires:
            http_cookie += '; Expires=' + expires.strftime(
                "%a, %d %b %Y %H:%M:%S GMT")
        if max_age:
            http_cookie += '; Max-Age=' + str(max_age)
        if secure:
            http_cookie += '; Secure'
        if http_only:
            http_cookie += '; HttpOnly'
        if 'Set-Cookie' in self.headers:
            self.headers['Set-Cookie'].append(http_cookie)
        else:
            self.headers['Set-Cookie'] = [http_cookie]

    def complete(self):
        if isinstance(self.body, bytes) and \
                'Content-Length' not in self.headers:
            self.headers['Content-Length'] = str(len(self.body))
        if 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = 'text/plain'

    def write(self, stream):
        self.complete()

        # status code
        reason = self.reason if self.reason is not None else \
            ('OK' if self.status_code == 200 else 'N/A')
        stream.write('HTTP/1.0 {status_code} {reason}\r\n'.format(
            status_code=self.status_code, reason=reason).encode())

        # headers
        for header, value in self.headers.items():
            values = value if isinstance(value, list) else [value]
            for value in values:
                stream.write('{header}: {value}\r\n'.format(
                    header=header, value=value).encode())
        stream.write(b'\r\n')

        # body
        can_flush = hasattr(stream, 'flush')
        try:
            for body in self.body_iter():
                if isinstance(body, str):
                    body = body.encode()
                stream.write(body)
                if can_flush:  # pragma: no cover
                    stream.flush()
        except OSError as exc:  # pragma: no cover
            if exc.errno == 32:  # errno.EPIPE
                pass
            else:
                raise

    def body_iter(self):
        if self.body:
            if hasattr(self.body, 'read'):
                while True:
                    buf = self.body.read(self.send_file_buffer_size)
                    if len(buf):
                        yield buf
                    if len(buf) < self.send_file_buffer_size:
                        break
                if hasattr(self.body, 'close'):  # pragma: no cover
                    self.body.close()
            elif hasattr(self.body, '__next__'):
                yield from self.body
            else:
                yield self.body

    @classmethod
    def redirect(cls, location, status_code=302):
        """Return a redirect response.

        :param location: The URL to redirect to.
        :param status_code: The 3xx status code to use for the redirect. The
                            default is 302.
        """
        if '\x0d' in location or '\x0a' in location:
            raise ValueError('invalid redirect URL')
        return cls(status_code=status_code, headers={'Location': location})

    @classmethod
    def send_file(cls, filename, status_code=200, content_type=None):
        """Send file contents in a response.

        :param filename: The filename of the file.
        :param status_code: The 3xx status code to use for the redirect. The
                            default is 302.
        :param content_type: The ``Content-Type`` header to use in the
                             response. If omitted, it is generated
                             automatically from the file extension.

        Security note: The filename is assumed to be trusted. Never pass
        filenames provided by the user before validating and sanitizing them
        first.
        """
        if content_type is None:
            ext = filename.split('.')[-1]
            if ext in Response.types_map:
                content_type = Response.types_map[ext]
            else:
                content_type = 'application/octet-stream'
        f = open(filename, 'rb')
        return cls(body=f, status_code=status_code,
                   headers={'Content-Type': content_type})

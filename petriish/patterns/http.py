from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class _RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path in self.server._post_handlers:
            response_body = self.server._post_handlers[self.path](
                self.rfile.read()
            )
            del self.server._post_handlers[self.path]
            self.send_response(HTTPStatus.OK)
            self.end_headers()
            self.wfile.write(response_body)
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")


class Server(ThreadingHTTPServer):
    def __init__(self, address):
        super().__init__(address, _RequestHandler)
        self._post_handlers = {}

    def add_post_handler(self, path, handler):
        if path in self._post_handlers:
            return False
        self._post_handlers[path] = handler
        return  True


class POSTTrigger(WorkflowPattern, namedtuple('POSTTrigger', ('server', 'path'))):
    name = 'post_trigger'

    @classmethod
    def from_data(cls, resources, data):
        return cls(
            server=resources[data['server']],
            path=data['path'],
        )

    def execute(self, input):
        data = None
        event = threading.Event()
        def handler(d):
            data = d
            event.set()
        self.server.add_post_handler(self.path, handler)
        event.wait()
        return Result(True, data)

    def output_type(self, resolver, input_type):
        resolver.unify(input_type, Record())
        return Bytes()


resources = [Server]
patterns = [POSTTrigger]

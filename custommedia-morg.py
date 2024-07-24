#!/usr/bin/python3
# CustomMedia but all requests are just sent to morg instead of trying to resolve the origin server
import urllib.request

class MyServer:
    def __init__(self, environ, start_response):
        self.environ = environ
        self.start_response = start_response

    def __iter__(self):
        hsp = "https://matrix.org" + self.environ['PATH_INFO'] + '?' + self.environ['QUERY_STRING']
        self.start_response('301 Moved Permanently', [('Location', hsp)])
        return iter([])

if __name__ == "__main__":
    from gunicorn.app.base import BaseApplication

    class GunicornServer(BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            for key, value in self.options.items():
                self.cfg.set(key, value)

        def load(self):
            return self.application

    options = {
        'bind': 'localhost:9999',
        'workers': 32,  # Adjust the number of workers based on your system's resources - ChatGPT
    }

    server = GunicornServer(MyServer, options)
    server.run()
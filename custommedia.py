#!/usr/bin/python3
import urllib.request
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
}

class MyServer:
    def __init__(self, environ, start_response):
        self.environ = environ
        self.start_response = start_response
        self.mapping_file = 'mapping.json'
        self.mappings = self.load_mappings()

    def __iter__(self):
        hs = self.environ['PATH_INFO'].split('/')[5]
        hsu = self.mappings.get(hs)

        if not hsu:
            wellknown = "https://" + hs + "/.well-known/matrix/client"
            req = urllib.request.Request(wellknown, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=2) as cont:
                    hsu = json.load(cont)
                    hsu = hsu["m.homeserver"]["base_url"]
                    self.mappings[hs] = hsu
                    self.save_mappings()
            except Exception as e: # I don't care to fix this properly, not my problem
                hsu = "https://matrix.org"

        hsu = hsu.rstrip('/')

        hsp = hsu + self.environ['PATH_INFO'] + '?' + self.environ['QUERY_STRING']
        self.start_response('301 Moved Permanently', [('Location', hsp)])
        return iter([])

    def load_mappings(self):
        try:
            with open(self.mapping_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_mappings(self):
        with open(self.mapping_file, 'w') as f:
            json.dump(self.mappings, f)

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
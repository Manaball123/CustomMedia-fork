#!/usr/bin/python3
import urllib.request
import json
import matrix_api
import cfg
import requests
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
}

def request_header_to_server_header(resp_header : dict) -> list:
    res = []
    for k in resp_header.keys():
        res.append((k, resp_header[k]))
    return res

#literally didnt refrence self at all
#heheheh boob
def check_token_valid(access_token, server_url = "http://localhost:8008"):
    resp = requests.post(
        url = f"{server_url}/_matrix/media/v1/create",
        headers={
            #no bearer because it would be forwarded too
            "Authorization" : access_token
        })
    return resp

class MyServer:
    def __init__(self, environ, start_response):
        self.environ = environ
        self.start_response = start_response
        self.mapping_file = 'mapping.json'
        self.mappings = self.load_mappings()
        #dont give enough of a shit to make the hs a config
        self.matrix_upload_client = matrix_api.MatrixClient(cfg.matrix_username, cfg. matrix_pass, cfg.matrix_device_id)
        #TODO: share one login token, and maybe pool accounts too
        if cfg.matrix_token == None:
            self.matrix_upload_client.login()
        else:       
            self.matrix_upload_client.login_with_token(cfg.matrix_token)

    
    
    def bad_request_400_resp(self):
        self.start_response('400 Bad Request', [])
        return iter([])
    
    def delegate_download(self):
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
        
    
    def delegate_upload(self):
        if not "HTTP_AUTHORIZATION" in self.environ.keys():
            self.start_response("403 Forbidden", [("Error", "give token >:(")])
            return iter([])
        
        token = self.environ["HTTP_AUTHORIZATION"]
        check_resp = check_token_valid(token)
        if check_resp.status_code != 200:
            #TODO: forward responses here
            if check_resp.status_code == 403:
                self.start_response("403 Forbidden", [("Error", "ur token is le bad")])
                return iter([check_resp.content])
            if check_resp.status_code == 429:
                self.start_response("429 Rate-limited", [("Error", "stop spamming this")])
                return iter(["test".encode('utf-8')])
            return self.bad_request_400_resp()
        #now upload thingy
        query_params = self.environ['QUERY_STRING']
        if query_params == None or query_params == "":
            query_params = "filename=file.bin"
        #now i COULD probably forward the stream directly but i dont know how to do that so u get this shit instead
        #thanks dude on SO https://stackoverflow.com/questions/530526/accessing-post-data-from-wsgi
        data = b""
        try:
            length = int(self.environ.get('CONTENT_LENGTH', '0'))
        except ValueError:
            length = 0
        if length != 0:
            data = self.environ['wsgi.input'].read(length)

        upload_resp = self.matrix_upload_client._upload_file(query_params.split("=")[1], data)
        #even though its the servers fault im still blaming it on client
        if upload_resp.status_code == 403:
            return self.bad_request_400_resp()
        #TODO: also forward this resp
        if upload_resp.status_code == 429:
            self.start_response("429 Rate-limited", [("Error", "bot was ratelimited but its now your problem")])
            return iter([upload_resp.content])
        
        if upload_resp.status_code == 200:
            self.start_response("200 Success", request_header_to_server_header(upload_resp.headers))
            return iter([upload_resp.content])
        
            

        
    def __iter__(self):
        endpoint = self.environ['PATH_INFO'].split('/')
        #TODO: add check for valid endpoints here
        if(len(endpoint) < 5):
            return self.bad_request_400_resp()
        
        if endpoint[4] == "upload":
            return self.delegate_upload()
        if endpoint[4] == "download" or endpoint[4] == "thumbnail":
            return self.delegate_download()
        
        return self.bad_request_400_resp()

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
        'workers': 4,  # Adjust the number of workers based on your system's resources - ChatGPT
    }

    server = GunicornServer(MyServer, options)
    server.run()
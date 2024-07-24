import requests



class MatrixClient:
    def __init__(self, username, password, device_id) -> None:
        self.logged_on = False
        self.hs_url = "https://matrix.org"
        self.username : str= username
        self.password : str = password
        self.device_id : str = device_id
    def login(self) -> bool:
        if self.logged_on:
            return True
        resp = requests.post(
            url = f"{self.hs_url}/_matrix/client/v3/login",
            json = {
            "device_id" : self.device_id,
            "identifier" : {
                "type" : "m.id.user",
                "user" : self.username,
            },
            "initial_device_display_name" : "bot",
            "password" : self.password,
            "type" : "m.login.password",
            "refresh_token" : False
        })
        if(resp.status_code == 200):
            resp = resp.json()
            self.token = resp["access_token"]
            self.logged_on = True
            return True
        return False



    #does not modify state of client, aka threadsafe(probably)
    def upload_file(self, name : str, data : bytes = None) -> str:
        if not self.logged_on:
            return None
        if data == None:
            with open(name, "rb") as f:
                data = f.read()
        resp = requests.post(
                        url = f"{self.hs_url}/_matrix/media/v3/upload",
                        data=data, 
                        params={"filename" : name}, 
                        headers={
                            'Content-Type': 'application/octet-stream',
                            "Authorization" : f"Bearer {self.token}"
                            })
        return resp.json()["content_uri"]
# CustomMedia

Prevent jews from stealing your matrix homeserver's precious storage space and bandwidth with this one simple webserver

# Requirements
- Python 3
- gunicorn - `pip3 install gunicorn`

# Nginx configuration
Add this inside of the block that matches for requests to /_matrix, replacing `server\.org` with your own homeserver
```
location ~ ^/_matrix/media/(?<folder>[^/]+)/((download|thumbnail)/(?!(server\.org)/))(?<file>.*)$ {
proxy_pass http://localhost:9999;
proxy_set_header X-Forwarded-For $remote_addr;
proxy_read_timeout 3600s;
add_header 'Access-Control-Allow-Origin' '*';
add_header 'Access-Control-Allow-Credentials' 'true';
add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS';
add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range';
}
```

# systemd Service
Place the remotemedia.py into /opt and give it permission to execute, then use this systemd service:
```
[Unit]
Description=Custom media
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=5
User=root
WorkingDirectory=/opt
ExecStart=/opt/custommedia.py

[Install]
WantedBy=multi-user.target
```

# Mappings
A mapping.json file will automatically be created in the non-matrix.org version. If you'd like to save your server a few unnecessary requests, then download the mapping.json from this repo and place it into the same directory as custommedia.py
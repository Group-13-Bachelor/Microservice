from flaskblog import create_app
from flaskblog.config import Config
import requests
import json
from flaskblog.models import Post

app = create_app(Config)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)

from flask import render_template, Blueprint
from flaskblog.models import Post
from datetime import datetime

import requests
import socket

main = Blueprint('main', __name__)


@main.route("/")
@main.route("/home")
def home():
    PostServiceIP = socket.gethostbyname("PostService")
    response = requests.get(f'http://{PostServiceIP}:5002/get_all')
    posts_raw = response.json()

    posts = []
    for post in posts_raw:
        posts.append(
            Post(
                id=post["id"],
                title=post["title"],
                date_posted=datetime.strptime(post["date_posted"], '%a, %d %b %Y %X %Z'),
                content=post["content"],
                user_id=post["user_id"],
                username=post["username"]
            )
        )
    return render_template('home.html', posts=posts)


@main.route("/about")
def about():
    return render_template('about.html', title='About')

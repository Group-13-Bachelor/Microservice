from flask import render_template, Blueprint
from flaskblog.models import Post
from datetime import datetime

import requests
import zmq
import json
import base64

main = Blueprint('main', __name__)

xsub_addr = 'tcp://127.0.0.1:5556'
context = zmq.Context()

socket_PUB = context.socket(zmq.PUB)
socket_PUB.connect(xsub_addr)

socket_REQ = context.socket(zmq.REQ)
socket_REQ.connect("tcp://127.0.0.1:5559")


@main.route("/")
@main.route("/home")
def home():
    # socket.send_multipart([b'posts_get_all_posts', b'blarg'])
    # xpub_addr = 'tcp://127.0.0.1:5555'
    # subscriberSocket = context.socket(zmq.SUB)
    # subscriberSocket.connect(xpub_addr)
    # subscriberSocket.setsockopt_string(zmq.SUBSCRIBE, "posts_get_all_posts_reply")
    #
    # if subscriberSocket.poll(timeout=10000):
    #     message = subscriberSocket.recv_multipart()
    #     print(f"{message}")
    # else:
    #     print("no reply...")

    socket_REQ.send(b"posts_get_all_posts")
    message_bytes = socket_REQ.recv()
    message_decoded = base64.b64decode(message_bytes).decode('utf8')
    json_acceptable_string = message_decoded.replace("'", "\"")
    message = json.loads(json_acceptable_string)

    posts = []
    for post in message:
        posts.append(
            Post(
                id=post["id"],
                title=post["title"],
                date_posted=datetime.strptime(post["date_posted"], '%a, %d %b %Y %X '),
                content=post["content"],
                user_id=post["user_id"],
                username=post["username"]
            )
        )
    print(f"{posts}")


    return render_template('home.html', posts=posts)
    # try:
    #     PostServiceIP = socket.gethostbyname("PostService")
    # except socket.gaierror:
    #     PostServiceIP = "192.168.123.141"
    #
    # response = requests.get(f'http://{PostServiceIP}:5002/get_all')
    # posts_raw = response.json()
    #
    # posts = []
    # for post in posts_raw:
    #     posts.append(
    #         Post(
    #             id=post["id"],
    #             title=post["title"],
    #             date_posted=datetime.strptime(post["date_posted"], '%a, %d %b %Y %X %Z'),
    #             content=post["content"],
    #             user_id=post["user_id"],
    #             username=post["username"]
    #         )
    #     )
    # return render_template('home.html', posts=posts)


@main.route("/about")
def about():
    socket_REQ.send(b"blarg")
    message = socket_REQ.recv()
    print(f"{message}")
    return render_template('about.html', title='About')

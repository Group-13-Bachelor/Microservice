from flask import render_template, Blueprint

# Local
from flaskblog.posts import controller

main = Blueprint('main', __name__)


@main.route("/")
@main.route("/home")
def home():
    posts = controller.get_all_posts()
    return render_template('home.html', posts=posts)


@main.route("/about")
def about():
    return render_template('about.html', title='About')

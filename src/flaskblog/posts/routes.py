from flask import (render_template, url_for, flash,
                   redirect, request, abort, Blueprint)

from flask_login import current_user, login_required
from flaskblog.models import Post
from flaskblog.posts.forms import PostForm

import flaskblog.posts.controller as cnt
posts = Blueprint('posts', __name__)


@posts.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post_route():
    form = PostForm()
    user = current_user
    post = Post(title=form.title.data, content=form.content.data, user_id=user.id, username=user.username)
    if form.validate_on_submit() and cnt.save_new_post(post):
        flash('Your post has been created!', 'success')
        return redirect(url_for('main.home'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post')


@posts.route("/post/<int:post_id>")
def post_route(post_id):
    post = cnt.get_post_id(post_id)

    return render_template('post.html', title=post.title, post=post)


@posts.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post_route(post_id):

    post = cnt.get_post_id(post_id)
    if post.user_id != current_user.id:
        abort(403)

    form = PostForm()
    if form.validate_on_submit():
        new_post = {
            "title": form.title.data,
            "content": form.content.data
        }
        print(f"new post:{new_post}")

        cnt.update_post(post, new_post)

        flash('Your post has been updated!', 'success')
        return redirect(url_for('posts.post_route', post_id=post.id))

    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content

    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post')


@posts.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post_route(post_id):
    post = cnt.get_post_id(post_id)

    if post.user_id != current_user.id:
        abort(403)

    if cnt.delete_post(post.id):
        flash('Your post has been deleted!', 'success')
    return redirect(url_for('main.home'))

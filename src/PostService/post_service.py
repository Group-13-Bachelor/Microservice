import flask
from flask import request, jsonify
from PostService import app, db
from PostService.model import Post

import sys


@app.route("/save_post", methods=['POST'])
def save_post():
	post_json = request.get_json()
	post = Post(
		title=post_json["title"],
		content=post_json["content"],
		user_id=post_json["user_id"],
		username=post_json["username"])
	db.session.add(post)
	db.session.commit()

	print(f"saved new post to db: {post}", file=sys.stdout)
	return jsonify(
		id=post.id,
		titl=post.title,
		date_posted=post.date_posted,
		content=post.content,
		user_id=post.user_id,
		username=post.username
	)


@app.route("/post/<int:post_id>")
def get_post_id(post_id):
	post = Post.query.get(post_id)
	return jsonify(
		id=post.id,
		title=post.title,
		date_posted=post.date_posted,
		content=post.content,
		user_id=post.user_id,
		username=post.username
	)


@app.route("/post/user/<int:user_id>")
def get_posts_by_user(user_id):
	posts = []
	for post in Post.query.filter_by(user_id=user_id).all():
		posts.append(
			{
				"id": post.id,
				"title": post.title,
				"date_posted": post.date_posted,
				"content": post.content,
				"user_id": post.user_id,
				"username": post.username
			}
		)
	return jsonify(posts)


@app.route("/get_all", methods=['GET'])
def get_all_posts():
	posts = []
	for post in Post.query.all():
		posts.append(
			{
				"id": post.id,
				"title": post.title,
				"date_posted": post.date_posted,
				"content": post.content,
				"user_id": post.user_id,
				"username": post.username
			}
		)
	return jsonify(posts)


@app.route("/update_post", methods=['POST'])
def update_post():
	post_json = request.get_json()

	post = Post.query.get(post_json["id"])
	post.title = post_json["title"]
	post.content = post_json["content"]

	db.session.commit()

	return jsonify(
		id=post.id,
		title=post.title,
		date_posted=post.date_posted,
		content=post.content,
		user_id=post.user_id,
		username=post.username
	)


@app.route("/delete_post", methods=['POST'])
def delete_post():
	post_json = request.get_json()
	post = Post.query.get(post_json["id"])

	db.session.delete(post)
	db.session.commit()
	return flask.Response(status=200)


def init_db():
	with app.app_context():
		db.drop_all()
		db.create_all()
		db.session.commit()

	posts = [
		Post(title="title 1", content="Content 1", user_id=1, username="user1"),
		Post(title="title 2", content="Content 2", user_id=2, username="user2"),
		Post(title="title 3", content="Content 31", user_id=3, username="user3"),
		Post(title="title 4", content="Content 32", user_id=3, username="user3")
	]

	for post in posts:
		db.session.add(post)
	db.session.commit()
	print("DB initialized:")
	print(Post.query.all())


if __name__ == '__main__':
	init_db()
	app.run(host='127.0.0.1', port=5002, debug=True)

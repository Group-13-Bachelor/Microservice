from flaskblog.models import Post
from datetime import datetime

import requests
import socket


def save_new_post(post: Post):
	post_data = {
		"title": post.title,
		"content": post.content,
		"user_id": post.user_id,
		"username": post.username
	}
	PostServiceIP = socket.gethostbyname("PostService")
	response = requests.post(f'http://{PostServiceIP}:5002/save_post', json=post_data)
	post_raw = response.json()

	post.id = post_raw["id"]
	post.date_posted = datetime.strptime(post_raw["date_posted"], '%a, %d %b %Y %X %Z')

	# db.session.add(post)
	# db.session.commit()
	# print(f"post after commit: {post}")

	return post


def get_post_id(post_id):
	# if post_id is not None:
	# 	# Super duper cache
	# 	post = Post.query.get(post_id)
	# 	if post:
	# 		return post
	PostServiceIP = socket.gethostbyname("PostService")
	print(f"post IP {PostServiceIP}")
	response = requests.get(f'http://{PostServiceIP}:5002/post/{post_id}')
	post_raw = response.json()

	post = Post(
		id=post_raw["id"],
		title=post_raw["title"],
		date_posted=datetime.strptime(post_raw["date_posted"], '%a, %d %b %Y %X %Z'),
		content=post_raw["content"],
		user_id=post_raw["user_id"],
		username=post_raw["username"]
	)
	return post


def update_post(post, new_post):
	post_data = {
		"id": post.id,
		"title": new_post["title"],
		"content": new_post["content"],
		"user_id": post.user_id,
		"username": post.username
	}

	PostServiceIP = socket.gethostbyname("PostService")
	response = requests.post(f'http://{PostServiceIP}:5002/update_post', json=post_data)
	post_raw = response.json()

	# post.title = post_raw["title"]
	# post.content = post_raw["content"]
	#
	# db.session.add(post)
	# db.session.commit()


def delete_post(post_id):
	post_data = {
		"id": post_id
	}
	PostServiceIP = socket.gethostbyname("PostService")
	requests.post(f'http://{PostServiceIP}:5002/delete_post', json=post_data)

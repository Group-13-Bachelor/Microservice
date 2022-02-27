from PostService.model import Post
from datetime import datetime

import requests


def save_new_post(post: Post):
	post_data = {
		"title": post.title,
		"content": post.content,
		"user_id": post.user_id,
		"username": post.username
	}
	print(f"new post: {post_data}")

	response = requests.post('http://127.0.0.1:5002/save_post', json=post_data)
	post_raw = response.json()
	print(f"raw post: {post_raw}")

	post.id = post_raw["id"]
	post.date_posted = datetime.strptime(post_raw["date_posted"], '%a, %d %b %Y %X %Z')
	print(f"post: {post}")

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

	response = requests.get(f'http://127.0.0.1:5002/post/{post_id}')
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
	print(f"Updated post data: {post_data}")

	response = requests.post('http://127.0.0.1:5002/update_post', json=post_data)
	post_raw = response.json()
	print(f"raw post: {post_raw}")

	# post.title = post_raw["title"]
	# post.content = post_raw["content"]
	#
	# print(f"post: {post}")
	# db.session.add(post)
	# db.session.commit()



def delete_post(post_id):
	post_data = {
		"id": post_id
	}
	requests.post('http://127.0.0.1:5002/delete_post', json=post_data)

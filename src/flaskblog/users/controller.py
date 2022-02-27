from flaskblog import db
from flaskblog.models import User, Post
from datetime import datetime

import requests


def register_user(user):
	new_user = {
		"username": user.username,
		"email": user.email,
		"password": user.password,
		"image_file": user.image_file
	}

	response = requests.post('http://127.0.0.1:5003/register_user', json=new_user)
	user_raw = response.json()

	user = User(
		id=user_raw["id"],
		username=user_raw["username"],
		email=user_raw["email"],
		image_file=user_raw["image_file"],
		password=user_raw["password"]
	)
	db.session.add(user)
	db.session.commit()


def get_user(**kwargs):
	data = None
	for key, value in kwargs.items():
		data = {key: value}

	if data is not None:
		# Super duper cache
		for key, value in data.items():
			user = User.query.filter_by(**{key: value}).first()
			if user:
				return user

		response = requests.get('http://127.0.0.1:5003/get_user', json=data)
		user_raw = response.json()

		user = User(
			id=user_raw["id"],
			username=user_raw["username"],
			email=user_raw["email"],
			image_file="default.jpg",
			password=user_raw["password"]
		)
		db.session.add(user)
		db.session.commit()
		return user


def get_users_posts(user_id):
	response = requests.get(f'http://127.0.0.1:5002/post/user/{user_id}')
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

	return posts

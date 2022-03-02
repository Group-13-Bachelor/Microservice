from flaskblog import db
from flaskblog.models import User, Post
from datetime import datetime

import requests
import socket


def register_user(user):
	new_user = {
		"username": user.username,
		"email": user.email,
		"password": user.password,
		"image_file": user.image_file
	}
	UserServiceIP = socket.gethostbyname("UserService")
	response = requests.post(f'http://{UserServiceIP}:5003/UserRegistered', json=new_user)
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


def update_user(current_user):
	new_user = {
		"id": current_user.id,
		"username": current_user.username,
		"email": current_user.email
	}


	UserServiceIP = socket.gethostbyname("UserService")
	requests.post(f'http://{UserServiceIP}:5003/UserUpdated', json=new_user)

	# Post service is also interested as it need to update the username of
	PostServiceIP = socket.gethostbyname("PostService")
	requests.post(f'http://{PostServiceIP}:5002/UserUpdated', json=new_user)


def get_user(**kwargs):
	"""
	    Keyword Args:
	        username (string): Users username
	        id (int): Users ID
	        email (string): Users Email
	"""
	data = None
	for key, value in kwargs.items():
		data = {key: value}

	if data is not None:
		# Super duper cache
		for key, value in data.items():
			user = User.query.filter_by(**{key: value}).first()
			if user:
				return user

		UserServiceIP = socket.gethostbyname("UserService")
		response = requests.get(f'http://{UserServiceIP}:5003/get_user', json=data)
		user_data = response.json()

		user = User(
			id=user_data["id"],
			username=user_data["username"],
			email=user_data["email"],
			image_file="default.jpg",
			password=user_data["password"]
		)
		db.session.add(user)
		db.session.commit()
		return user


def get_users_posts(user_id):
	PostServiceIP = socket.gethostbyname("PostService")
	response = requests.get(f'http://{PostServiceIP}:5002/post/user/{user_id}')
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

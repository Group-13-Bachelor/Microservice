from flask import request, jsonify, Response
from UserService import app, db
from UserService.model import User
from flask_bcrypt import Bcrypt


@app.route("/register_user", methods=['POST'])
def register_user():
	user_json = request.get_json()
	user = User(
		username=user_json["username"],
		email=user_json["email"],
		image_file=user_json["image_file"],
		password=user_json["password"])
	db.session.add(user)
	db.session.commit()

	return jsonify(
		id=user.id,
		username=user.username,
		email=user.email,
		image_file=user.image_file,
		password=user.password
	)


@app.route("/get_user", methods=['GET'])
def get_user():
	body = request.get_json()
	user = None
	if "username" in body:
		user = User.query.filter_by(username=body["username"]).first()
	elif "id" in body:
		user = User.query.filter_by(id=body["id"]).first()
	elif "email" in body:
		user = User.query.filter_by(email=body["email"]).first()

	if user is not None:
		return jsonify(
			id=user.id,
			username=user.username,
			email=user.email,
			image_file=user.image_file,
			password=user.password)
	else:
		return Response(status=404)


def init_db():
	with app.app_context():
		db.drop_all()
		db.create_all()
		db.session.commit()

	bcrypt = Bcrypt()

	users = [
		User(username="user1", email="user1@email.mail", password=bcrypt.generate_password_hash("123").decode('utf-8')),
		User(username="user2", email="user2@email.mail", password=bcrypt.generate_password_hash("123").decode('utf-8')),
		User(username="user3", email="user3@email.mail", password=bcrypt.generate_password_hash("123").decode('utf-8'))
	]
	for user in users:
		db.session.add(user)
	db.session.commit()
	print("DB initialized")
	print(User.query.all())


if __name__ == '__main__':
	init_db()
	app.run(host='0.0.0.0', port=5003, debug=True)

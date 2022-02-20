from datetime import datetime
from PostService import db


class Post(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(100), nullable=False)
	date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
	content = db.Column(db.Text, nullable=False)
	user_id = db.Column(db.Integer, nullable=False)
	username = db.Column(db.String(20), nullable=False)
	image_file = db.Column(db.String(20), nullable=False, default='default.jpg')

	def __repr__(self):
		return f"Post('{self.id}', '{self.title}', '{self.date_posted}', '{self.user_id}', '{self.username}')"

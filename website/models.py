from website import db
from flask_login import UserMixin
from datetime import datetime, timezone, timedelta

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(150))
    date_joined = db.Column(db.DateTime, default=datetime.now(timezone.utc) + timedelta(hours=1))
    exercises = db.relationship('Exercise', backref='user', lazy=True, cascade="all, delete-orphan")
    posts = db.relationship('Post', backref='user', lazy=True, cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='user', lazy=True, cascade="all, delete-orphan")
    chat_messages = db.relationship('ChatMessage', backref='user', lazy=True, cascade="all, delete-orphan")

class ExerciseLibrary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(20))
    duration_minutes = db.Column(db.Integer)
    calories_burned = db.Column(db.Integer)
    requires_equipment = db.Column(db.Boolean, default=False)
    equipment_needed = db.Column(db.String(200))
    exercise_type = db.Column(db.String(50))
    instructions = db.Column(db.Text)
    benefits = db.Column(db.Text)
    image_url = db.Column(db.String(200))

class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(100))
    duration_minutes = db.Column(db.Integer)
    calories_burned = db.Column(db.Integer)
    exercise_type = db.Column(db.String(100))
    date_completed = db.Column(db.DateTime, default=datetime.now(timezone.utc) + timedelta(hours=1))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.String(500))
    likes = db.relationship('Like', backref='post', lazy=True, cascade="all, delete-orphan")
    
    def like_count(self):
        return len(self.likes)
    
    def is_liked_by(self, user):
        return any(like.user_id == user.id for like in self.likes)
    
    date = db.Column(db.DateTime, default=datetime.now(timezone.utc) + timedelta(hours=1))
    comments = db.relationship('Comment', backref='post', lazy=True, cascade="all, delete-orphan")

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    content = db.Column(db.String(300))
    date = db.Column(db.DateTime, default=datetime.now(timezone.utc) + timedelta(hours=1))

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.String(500))
    sender = db.Column(db.String(20))
    date = db.Column(db.DateTime, default=datetime.now(timezone.utc) + timedelta(hours=1))
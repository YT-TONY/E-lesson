from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'student', 'teacher', 'admin'
    is_approved = db.Column(db.Boolean, default=False)  # new column 

    notes = db.relationship('Note', backref='uploader', lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"

class Note(db.Model):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(200), nullable=False)
    course = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='pending') 
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f"<Note {self.title} - {self.status}>"

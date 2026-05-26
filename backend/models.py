from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    profile = db.relationship('Profile', backref='user', uselist=False, cascade='all, delete-orphan')
    survey = db.relationship('SurveyAnswer', backref='user', uselist=False, cascade='all, delete-orphan')
    liked_anime = db.relationship('LikedAnime', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    watched_anime = db.relationship('WatchedAnime', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    ratings = db.relationship('Rating', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Anime(db.Model):
    __tablename__ = 'anime'
    id = db.Column(db.Integer, primary_key=True)
    mal_id = db.Column(db.Integer, unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    english_name = db.Column(db.String(255), nullable=True)
    japanese_name = db.Column(db.String(255), nullable=True)
    score = db.Column(db.Float, nullable=True)
    genres = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    synopsis = db.Column(db.Text, nullable=True)
    scored_by = db.Column(db.Integer, default=0, nullable=True)

class Profile(db.Model):
    __tablename__ = 'profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bio = db.Column(db.Text, nullable=True)

class LikedAnime(db.Model):
    __tablename__ = 'liked_anime'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    anime_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=True)

class WatchedAnime(db.Model):
    __tablename__ = 'watched_anime'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    anime_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=True)

class SurveyAnswer(db.Model):
    __tablename__ = 'survey_answers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    genres = db.Column(db.String(255), nullable=True) # e.g., "Action,Romance"
    min_score = db.Column(db.Float, nullable=True)
    max_episodes = db.Column(db.Integer, nullable=True)
    preferred_year = db.Column(db.Integer, nullable=True)

class Rating(db.Model):
    __tablename__ = 'ratings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    anime_id = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False) # 1-10
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

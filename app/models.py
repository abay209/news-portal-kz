from datetime import datetime
from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=True)
    email = db.Column(db.String(120), index=True, unique=True, nullable=True)
    phone_number = db.Column(db.String(20), index=True, unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=True)
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    facebook_id = db.Column(db.String(100), unique=True, nullable=True)
    avatar_url = db.Column(db.String(300), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class Source(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    url = db.Column(db.String(500), unique=True, nullable=False)
    source_type = db.Column(db.String(50), default='rss') # rss, api, etc
    is_active = db.Column(db.Boolean, default=True)
    last_fetched = db.Column(db.DateTime, nullable=True)
    language = db.Column(db.String(2), default='ru') # default source language

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    # The name of the category will be handled via translations based on 'code'
    news = db.relationship('News', backref='category', lazy='dynamic')

news_tags = db.Table('news_tags',
    db.Column('news_id', db.Integer, db.ForeignKey('news.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    
    title_kk = db.Column(db.String(200), nullable=False)
    title_ru = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200), nullable=False)
    
    content_kk = db.Column(db.Text, nullable=False)
    content_ru = db.Column(db.Text, nullable=False)
    content_en = db.Column(db.Text, nullable=False)
    
    summary_kk = db.Column(db.Text, nullable=True)
    summary_ru = db.Column(db.Text, nullable=True)
    summary_en = db.Column(db.Text, nullable=True)
    
    image_filename = db.Column(db.String(200), nullable=True)
    
    source_name = db.Column(db.String(100), nullable=True)
    original_url = db.Column(db.String(500), unique=True, nullable=True)
    
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    comments = db.relationship('Comment', backref='news', lazy='dynamic', cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary=news_tags, backref=db.backref('news', lazy='dynamic'))
    poll = db.relationship('Poll', backref='news', uselist=False, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'category_code': self.category.code if self.category else '',
            'title_kk': self.title_kk,
            'title_ru': self.title_ru,
            'title_en': self.title_en,
            'content_kk': self.content_kk,
            'content_ru': self.content_ru,
            'content_en': self.content_en,
            'summary_kk': self.summary_kk,
            'summary_ru': self.summary_ru,
            'summary_en': self.summary_en,
            'image_filename': self.image_filename,
            'source_name': self.source_name,
            'original_url': self.original_url,
            'views': self.views,
            'created_at': self.created_at.isoformat()
        }

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    news_id = db.Column(db.Integer, db.ForeignKey('news.id'), nullable=False)
    
    # Guest comments if not logged in (optional)
    guest_name = db.Column(db.String(100), nullable=True)

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    news_id = db.Column(db.Integer, db.ForeignKey('news.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('bookmarks', lazy='dynamic', cascade='all, delete-orphan'))
    news = db.relationship('News', backref=db.backref('bookmarks', lazy='dynamic', cascade='all, delete-orphan'))

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    news_id = db.Column(db.Integer, db.ForeignKey('news.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('likes', lazy='dynamic', cascade='all, delete-orphan'))
    news = db.relationship('News', backref=db.backref('likes', lazy='dynamic', cascade='all, delete-orphan'))

class ViewHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # None for guests
    session_id = db.Column(db.String(100), nullable=True) # To track guests over a session
    news_id = db.Column(db.Integer, db.ForeignKey('news.id'), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('view_history', lazy='dynamic', cascade='all, delete-orphan'))
    news = db.relationship('News', backref=db.backref('view_history', lazy='dynamic', cascade='all, delete-orphan'))

class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    news_id = db.Column(db.Integer, db.ForeignKey('news.id'), nullable=False)
    question = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    options = db.relationship('PollOption', backref='poll', lazy='dynamic', cascade='all, delete-orphan')
    votes_record = db.relationship('PollVote', backref='poll', lazy='dynamic', cascade='all, delete-orphan')

class PollOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    text = db.Column(db.String(200), nullable=False)
    votes = db.Column(db.Integer, default=0)

class PollVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # If logged in
    ip_address = db.Column(db.String(50), nullable=True) # To prevent duplicate votes for guests
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


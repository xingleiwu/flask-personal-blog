from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import pytz

db = SQLAlchemy()

CST = pytz.timezone('Asia/Shanghai')

def utc_to_cst(utc_time):
    if utc_time is None:
        return None
    if utc_time.tzinfo is None:
        utc_time = pytz.utc.localize(utc_time)
    return utc_time.astimezone(CST)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def created_at_cst(self):
        return utc_to_cst(self.created_at)

    @property
    def updated_at_cst(self):
        return utc_to_cst(self.updated_at)

    def format_time(self, time_obj, fmt='%Y-%m-%d %H:%M'):
        cst_time = utc_to_cst(time_obj)
        return cst_time.strftime(fmt) if cst_time else ''

    def __repr__(self):
        return f'<Article {self.title}>'

class SiteSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(200), nullable=False)

    @staticmethod
    def get(key, default=None):
        setting = SiteSetting.query.filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set(key, value):
        setting = SiteSetting.query.filter_by(key=key).first()
        if setting:
            setting.value = str(value)
        else:
            setting = SiteSetting(key=key, value=str(value))
            db.session.add(setting)
        db.session.commit()

class AdminUser(UserMixin):
    def __init__(self, username):
        self.id = username
        self.username = username

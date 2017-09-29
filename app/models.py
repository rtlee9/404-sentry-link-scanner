"""Data models for link check scans"""
from . import db
from passlib.apps import custom_app_context as pwd_context


class Link(db.Model):
    """Data model representing a request and response for single link"""
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Text, index=True)
    source_url = db.Column(db.Text, index=True)
    job_id = db.Column(db.Integer, db.ForeignKey('scan_job.id'))

    def __repr__(self):
        return '<{} --> {}>'.format(self.source_url, self.url)


class LinkCheck(db.Model):
    """Data model representing a request and response for single link"""
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Text, index=True)
    url_raw = db.Column(db.Text)
    response = db.Column(db.Integer, index=True)
    note = db.Column(db.Text)
    text = db.Column(db.Text)
    job_id = db.Column(db.Integer, db.ForeignKey('scan_job.id'))

    def __repr__(self):
        return '<URL {}: {}>'.format(self.url, self.response)

class ScanJob(db.Model):
    """Data model representing a request and response for single link"""
    id = db.Column(db.Integer, primary_key=True)
    root_url = db.Column(db.Text, index=True)
    start_time = db.Column(db.DateTime)
    link_checks = db.relationship('LinkCheck', backref='job', lazy='dynamic')
    links = db.relationship('Link', backref='job', lazy='dynamic')

    def __repr__(self):
        return '<URL {} {}>'.format(self.root_url, self.start_time)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(32), index = True)
    password_hash = db.Column(db.String(128))

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def __repr__(self):
        return '<User {}>'.format(self.username)

"""Data models for link check scans"""
from . import db
from passlib.apps import custom_app_context as pwd_context
from sqlalchemy import UniqueConstraint


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

    def to_json(self):
        return dict(
            id=self.id,
            url=self.url_raw,
            response=self.response,
            note=self.note,
            job_id=self.job_id,
        )


class ScheduledJob(db.Model):
    """Data model representing a request and response for single link"""
    id = db.Column(db.Integer, primary_key=True)
    root_url = db.Column(db.Text, index=True)
    owner = db.Column(db.Text, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return '<{} {}>'.format(self.owner, self.root_url)

    def to_json(self):
        return dict(
            id=self.id,
            root_url=self.root_url,
            owner=self.owner,
            user_id=self.user_id,
        )


class ScanJob(db.Model):
    """Data model representing a request and response for single link"""
    id = db.Column(db.Integer, primary_key=True)
    root_url = db.Column(db.Text, index=True)
    start_time = db.Column(db.DateTime)
    link_checks = db.relationship('LinkCheck', backref='job', lazy='dynamic')
    links = db.relationship('Link', backref='job', lazy='dynamic')
    owner = db.Column(db.Text, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.Text)

    def __repr__(self):
        return '<URL {} {}: {}>'.format(self.root_url, self.start_time, self.status)

    def to_json(self):
        return dict(
            id=self.id,
            root_url=self.root_url,
            start_time=self.start_time,
            owner=self.owner,
            user_id=self.user_id,
            status=self.status,
        )


class PermissionedURL(db.Model):
    __tablename__ = 'permissioned_url'
    """Data model representing a request and response for single link"""
    id = db.Column(db.Integer, primary_key=True)
    root_url = db.Column(db.Text, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    owner = db.Column(db.Text, index=True)
    __table_args__ = (UniqueConstraint(
        'root_url',
        'user_id',
        'owner',
        name='unique_urls_per_userowner'),)

    def __repr__(self):
        return '<{} {}>'.format(self.owner, self.root_url)

    def to_json(self):
        return dict(
            id=self.id,
            root_url=self.root_url,
            user_id=self.user_id,
            owner=self.owner,
        )


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(32), index = True)
    admin = db.Column(db.Boolean)
    password_hash = db.Column(db.String(128))
    scan_jobs = db.relationship('ScanJob', backref='user', lazy='dynamic')
    scheduled_jobs = db.relationship('ScheduledJob', backref='user', lazy='dynamic')
    permissioned_urls = db.relationship('PermissionedURL', backref='user', lazy='dynamic')

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def __repr__(self):
        return '<User {}>'.format(self.username)

"""Data models for link check scans"""
from . import db
from passlib.apps import custom_app_context as pwd_context
from sqlalchemy import UniqueConstraint


class Link(db.Model):
    """Data model representing a request and response for single link"""
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Text, index=True)
    source_url = db.Column(db.Text, index=True)
    job_id = db.Column(db.Integer, db.ForeignKey('scan_job.id'), nullable=False)

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
    exception = db.Column(db.String(20), index=True)
    job_id = db.Column(db.Integer, db.ForeignKey('scan_job.id'), nullable=False)

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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('owners.id'), nullable=False)

    def __repr__(self):
        return '<Scheduled job {} [{}/{}]>'.format(
            self.root_url,
            self.user_id,
            self.owner_id
        )

    def to_json(self):
        return dict(
            id=self.id,
            root_url=self.root_url,
            owner_id=self.owner_id,
            user_id=self.user_id,
        )


class ScanJob(db.Model):
    """Data model representing a request and response for single link"""
    id = db.Column(db.Integer, primary_key=True)
    root_url = db.Column(db.Text, index=True)
    start_time = db.Column(db.DateTime, nullable=False)
    link_checks = db.relationship('LinkCheck', backref='job', lazy='dynamic')
    links = db.relationship('Link', backref='job', lazy='dynamic')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('owners.id'), nullable=False)
    status = db.Column(db.Text)

    def __repr__(self):
        return '<URL {} {}: {}>'.format(self.root_url, self.start_time, self.status)

    def to_json(self):
        return dict(
            id=self.id,
            root_url=self.root_url,
            start_time=self.start_time,
            owner_id=self.owner_id,
            user_id=self.user_id,
            status=self.status,
        )


class PermissionedURL(db.Model):
    __tablename__ = 'permissioned_url'
    """Data model representing a request and response for single link"""
    id = db.Column(db.Integer, primary_key=True)
    stripe_subscription_id = db.Column(db.String(32))
    root_url = db.Column(db.Text, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('owners.id'), nullable=False)
    __table_args__ = (UniqueConstraint(
        'root_url',
        'user_id',
        'owner_id',
        name='unique_urls_per_userowner'),)

    def __repr__(self):
        return '<Permissioned URL {} [{}/{}]>'.format(
            self.root_url,
            self.user_id,
            self.owner_id
        )

    def to_json(self):
        return dict(
            id=self.id,
            root_url=self.root_url,
            user_id=self.user_id,
            owner_id=self.owner_id,
            stripe_subscription_id=self.stripe_subscription_id
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
    owners = db.relationship('Owner', backref='user', lazy='dynamic')

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Owner(db.Model):
    __tablename__ = 'owners'
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(50), index = True)
    stripe_token = db.Column(db.Text)
    stripe_email = db.Column(db.String(50))
    stripe_customer_id = db.Column(db.String(50))
    scan_jobs = db.relationship('ScanJob', backref='owner', lazy='dynamic')
    scheduled_jobs = db.relationship('ScheduledJob', backref='owner', lazy='dynamic')
    permissioned_urls = db.relationship('PermissionedURL', backref='owner', lazy='dynamic')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    __table_args__ = (UniqueConstraint(
        'email',
        'user_id',
        name='unique_user_owners'),)

    def __repr__(self):
        return '<Owner {}>'.format(self.email)

    def to_json(self):
        return dict(
            id=self.id,
            email=self.email,
            stripe_token=self.stripe_token,
            stripe_email=self.stripe_email,
            stripe_customer_id=self.stripe_customer_id,
        )


class Exception(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exception = db.Column(db.Text, index=True, unique=True)
    exception_description = db.Column(db.Text, index=True)

    def __repr__(self):
        return '<Exception {}: {}>'.format(self.exception, self.excpetion_description)

    def to_json(self):
        return dict(
            id=self.id,
            exception=self.exception,
            exception_description=self.exception_description,
        )

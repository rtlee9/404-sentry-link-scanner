"""Data models for link check scans"""
from . import db


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

    def __repr__(self):
        return '<URL {} {}>'.format(self.root_url, self.start_time)

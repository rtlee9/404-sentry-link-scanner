"""Data models for link check scans"""
from . import db
from sqlalchemy.dialects.postgresql import JSON


class LinkCheck(db.Model):
    """Data model representing a request and response for single link"""
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Text, index=True)
    response = db.Column(db.Integer, index=True)
    headers = db.Column(JSON)
    note = db.Column(db.Text)

    def __repr__(self):
        return '<URL {}: {}>'.format(self.url, self.response)

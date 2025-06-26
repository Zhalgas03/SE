from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy (do this in your app.py as well)
db = SQLAlchemy()

class Trip(db.Model):
    __tablename__ = 'trips'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    pdf_path = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    voting_rule = db.relationship('VotingRule', back_populates='trip', uselist=False, cascade="all, delete-orphan")
    votes = db.relationship('Vote', back_populates='trip', cascade="all, delete-orphan")

class VotingRule(db.Model):
    __tablename__ = 'voting_rules'
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False, unique=True)
    threshold = db.Column(db.Integer, nullable=False)
    min_votes = db.Column(db.Integer, nullable=False)
    max_votes = db.Column(db.Integer, nullable=False)
    trip = db.relationship('Trip', back_populates='voting_rule')

class Vote(db.Model):
    __tablename__ = 'votes'
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    session_token = db.Column(db.String(128), nullable=False)
    value = db.Column(db.Integer, nullable=False)  # or Boolean if you prefer
    trip = db.relationship('Trip', back_populates='votes')
    __table_args__ = (
        db.UniqueConstraint('trip_id', 'session_token', name='unique_vote_per_trip_session'),
    ) 
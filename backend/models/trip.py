<<<<<<< HEAD
"""
SQLAlchemy Models for Trip Management System

This module defines the database models for trips, voting rules, and votes.
All models are designed to be compatible with the existing raw SQL logic
and provide proper relationships and constraints.

Models:
- Trip: Main trip entity with creator relationship
- VotingRule: Voting configuration for trips
- Vote: Individual votes on trips (supports both authenticated users and guests)
- TripGroup: Many-to-many relationship between users and trips

Dependencies:
- SQLAlchemy 2.0+
- PostgreSQL (for JSON fields and advanced constraints)
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Enum, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class VoteType(enum.Enum):
    """Enumeration for vote values"""
    YES = 1
    NO = -1

class TripStatus(enum.Enum):
    """Enumeration for trip status"""
    DRAFT = "draft"
    PENDING_VOTE = "pending_vote"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class UserRole(enum.Enum):
    """Enumeration for user roles in trip groups"""
    CREATOR = "creator"
    MEMBER = "member"
    ADMIN = "admin"

class Trip(Base):
    """
    Trip model representing a travel plan
    
    This model matches the schema expected by the raw SQL in:
    - backend/api/trips.py (create_trip, get_trips)
    - backend/api/voting_rules.py (create_voting_rule)
    - backend/api/votes.py (vote_on_trip)
    
    Relationships:
    - creator: One-to-many with User (via creator_id)
    - voting_rule: One-to-one with VotingRule
    - votes: One-to-many with Vote
    - trip_group: One-to-many with TripGroup
    """
    __tablename__ = 'trips'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Basic trip information
    name = Column(String(255), nullable=False, comment="Trip name (required)")
    description = Column(Text, comment="Optional trip description")
    
    # Creator relationship (matches raw SQL: creator_id)
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment="ID of the user who created this trip")
    
    # Trip dates
    date_start = Column(DateTime, comment="Trip start date")
    date_end = Column(DateTime, comment="Trip end date")
    
    # Trip status (new field for enhanced functionality)
    status = Column(Enum(TripStatus), default=TripStatus.DRAFT, comment="Current status of the trip")
    
    # PDF file information (new fields for /api/save_trip functionality)
    pdf_file_path = Column(String(500), comment="Path to stored PDF file on server")
    pdf_file_name = Column(String(255), comment="Original filename of uploaded PDF")
    pdf_file_size = Column(Integer, comment="Size of PDF file in bytes")
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), comment="Timestamp when trip was created")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="Timestamp when trip was last updated")
    
    # Relationships
    creator = relationship("User", back_populates="created_trips", foreign_keys=[creator_id])
    voting_rule = relationship("VotingRule", back_populates="trip", uselist=False, cascade="all, delete-orphan")
    votes = relationship("Vote", back_populates="trip", cascade="all, delete-orphan")
    trip_group = relationship("TripGroup", back_populates="trip", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Trip(id={self.id}, name='{self.name}', creator_id={self.creator_id})>"

class VotingRule(Base):
    """
    Voting rule model for trip voting configuration
    
    This model matches the schema expected by the raw SQL in:
    - backend/api/voting_rules.py (create_voting_rule)
    - backend/api/votes.py (vote_on_trip)
    
    Relationships:
    - trip: One-to-one with Trip
    """
    __tablename__ = 'voting_rules'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Trip relationship (unique constraint ensures one rule per trip)
    trip_id = Column(Integer, ForeignKey('trips.id'), nullable=False, unique=True, comment="ID of the trip this rule applies to")
    
    # Voting configuration
    approval_threshold = Column(Float, nullable=False, default=0.7, comment="Percentage of yes votes required for approval (0.0 to 1.0)")
    min_votes_required = Column(Integer, nullable=False, default=3, comment="Minimum number of votes required before determining outcome")
    max_votes_allowed = Column(Integer, comment="Maximum number of votes allowed (optional)")
    duration_hours = Column(Integer, nullable=False, default=24, comment="Voting duration in hours from trip creation")
    rule_type = Column(String(50), default='majority', comment="Type of voting rule (majority, unanimous, etc.)")
    
    # Voting period (optional explicit start/end times)
    voting_start = Column(DateTime, comment="Explicit voting start time (optional)")
    voting_end = Column(DateTime, comment="Explicit voting end time (optional)")
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), comment="Timestamp when voting rule was created")
    
    # Relationships
    trip = relationship("Trip", back_populates="voting_rule")
    
    def __repr__(self):
        return f"<VotingRule(id={self.id}, trip_id={self.trip_id}, threshold={self.approval_threshold})>"

class Vote(Base):
    """
    Vote model for individual votes on trips
    
    This model supports both authenticated users and guest voting via session tokens.
    It matches the schema expected by the raw SQL in:
    - backend/api/votes.py (vote_on_trip)
    
    Relationships:
    - trip: Many-to-one with Trip
    - user: Many-to-one with User (optional, for authenticated votes)
    """
    __tablename__ = 'votes'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Trip relationship
    trip_id = Column(Integer, ForeignKey('trips.id'), nullable=False, comment="ID of the trip being voted on")
    
    # Voter identification (either user_id OR session_token must be provided)
    user_id = Column(Integer, ForeignKey('users.id'), comment="ID of authenticated user (optional for guest voting)")
    session_token = Column(String(255), comment="Session token for guest voting (optional for authenticated users)")
    
    # Vote data
    value = Column(Integer, nullable=False, comment="Vote value: 1 for YES, -1 for NO")
    comment = Column(Text, comment="Optional comment with the vote")
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), comment="Timestamp when vote was submitted")
    
    # Relationships
    trip = relationship("Trip", back_populates="votes")
    user = relationship("User", back_populates="votes")
    
    def __repr__(self):
        voter = f"user_id={self.user_id}" if self.user_id else f"session_token={self.session_token[:8]}..."
        return f"<Vote(id={self.id}, trip_id={self.trip_id}, {voter}, value={self.value})>"

class TripGroup(Base):
    """
    Trip group model for many-to-many relationship between users and trips
    
    This model matches the schema expected by the raw SQL in:
    - backend/api/trips.py (create_trip, get_trips)
    
    Relationships:
    - trip: Many-to-one with Trip
    - user: Many-to-one with User
    """
    __tablename__ = 'trip_group'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Relationships
    trip_id = Column(Integer, ForeignKey('trips.id'), nullable=False, comment="ID of the trip")
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment="ID of the user")
    
    # User role in the trip
    role = Column(Enum(UserRole), default=UserRole.MEMBER, comment="Role of the user in this trip")
    
    # Metadata
    joined_at = Column(DateTime, default=func.now(), comment="Timestamp when user joined the trip")
    
    # Relationships
    trip = relationship("Trip", back_populates="trip_group")
    user = relationship("User", back_populates="trip_memberships")
    
    def __repr__(self):
        return f"<TripGroup(id={self.id}, trip_id={self.trip_id}, user_id={self.user_id}, role={self.role})>"

# User model (assuming it exists, adding relationships)
class User(Base):
    """
    User model (assumed to exist in the database)
    
    This model defines relationships with the trip system.
    The actual User model should be defined elsewhere or imported.
    """
    __tablename__ = 'users'
    
    # Primary key (matches raw SQL expectations)
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False, comment="Unique username")
    email = Column(String(255), unique=True, nullable=False, comment="Unique email address")
    password_hash = Column(String(255), comment="Hashed password")
    
    # Additional fields (if they exist in the current schema)
    is_2fa_enabled = Column(Boolean, default=False, comment="Whether 2FA is enabled for this user")
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), comment="Timestamp when user was created")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="Timestamp when user was last updated")
    
    # Relationships
    created_trips = relationship("Trip", back_populates="creator", foreign_keys="Trip.creator_id")
    votes = relationship("Vote", back_populates="user")
    trip_memberships = relationship("TripGroup", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

# Import all models for easy access
__all__ = ['Base', 'Trip', 'VotingRule', 'Vote', 'TripGroup', 'User', 'TripStatus', 'VoteType', 'UserRole']
=======
from datetime import datetime, timezone
from . import db  # Use the shared db instance

class Trip(db.Model):
    __tablename__ = 'trips'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    pdf_path = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
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
>>>>>>> 276f72e77590322f9f8c422c79f4ba32443e7c4f

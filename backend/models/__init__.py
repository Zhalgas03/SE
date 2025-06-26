from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .trip import Trip, VotingRule, Vote

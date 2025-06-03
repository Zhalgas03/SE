from sqlalchemy import Column, String
from db import Base

class User(Base):
    __tablename__ = "users"
    email = Column(String, primary_key=True, unique=True, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)

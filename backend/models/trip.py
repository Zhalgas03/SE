from sqlalchemy import Column, Integer, String, Date, ForeignKey
from db import Base

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    date_start = Column(Date, nullable=False)
    date_end = Column(Date, nullable=False)
    creator_email = Column(String, ForeignKey("users.email"), nullable=False)

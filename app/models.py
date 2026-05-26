from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    target_score = Column(Integer)
    created_by = Column(Integer, ForeignKey("users.id"))
    is_finished = Column(Boolean, default=False)
    loser = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    players = relationship("Player", back_populates="match")
    rounds = relationship("Round", back_populates="match")


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    total_score = Column(Integer, default=0)

    match_id = Column(Integer, ForeignKey("matches.id"))

    match = relationship("Match", back_populates="players")


class Round(Base):
    __tablename__ = "rounds"

    id = Column(Integer, primary_key=True)
    round_number = Column(Integer)

    match_id = Column(Integer, ForeignKey("matches.id"))

    match = relationship("Match", back_populates="rounds")
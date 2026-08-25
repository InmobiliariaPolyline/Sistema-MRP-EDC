# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_token = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    username = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default="cliente")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)

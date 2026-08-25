from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime

class FailedLoginAttempt(Base):
    """Track failed login attempts for security"""
    __tablename__ = "failed_login_attempts"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False)
    ip_address = Column(String(50), nullable=True)
    attempt_time = Column(DateTime, default=datetime.utcnow)
    reason = Column(String(255), nullable=True)  # wrong password, user not found, etc
    
    def __repr__(self):
        return f"<FailedLoginAttempt(username={self.username}, time={self.attempt_time})>"

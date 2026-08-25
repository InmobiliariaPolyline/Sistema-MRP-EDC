from sqlalchemy.orm import Session
from sqlalchemy import func
from models.login_log import LoginLog
from models.failed_login import FailedLoginAttempt
from datetime import datetime, timedelta

def log_login(db: Session, user_id: int, username: str, ip_address: str = None):
    """Register a login event"""
    login_log = LoginLog(
        user_id=user_id,
        username=username,
        login_time=datetime.utcnow(),
        ip_address=ip_address
    )
    db.add(login_log)
    db.commit()
    db.refresh(login_log)
    return login_log

def get_login_logs(db: Session, limit: int = 50):
    """Get recent login logs"""
    return db.query(LoginLog).order_by(LoginLog.login_time.desc()).limit(limit).all()

def get_user_login_history(db: Session, user_id: int, limit: int = 20):
    """Get login history for a specific user"""
    return db.query(LoginLog).filter(LoginLog.user_id == user_id).order_by(LoginLog.login_time.desc()).limit(limit).all()

def get_failed_attempts(db: Session, limit: int = 200):
    """Get recent failed login attempts ordered by time desc."""
    return (
        db.query(FailedLoginAttempt)
        .order_by(FailedLoginAttempt.attempt_time.desc())
        .limit(limit)
        .all()
    )

def get_locked_accounts(db: Session):
    """Returns list of (username, count) for accounts locked right now (≥5 fails in 15 min)."""
    lockout_time = datetime.utcnow() - timedelta(minutes=15)
    return (
        db.query(
            FailedLoginAttempt.username,
            func.count(FailedLoginAttempt.id).label("count"),
        )
        .filter(FailedLoginAttempt.attempt_time > lockout_time)
        .group_by(FailedLoginAttempt.username)
        .having(func.count(FailedLoginAttempt.id) >= 5)
        .all()
    )

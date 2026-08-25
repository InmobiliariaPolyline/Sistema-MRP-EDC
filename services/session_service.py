# -*- coding: utf-8 -*-
import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.session import UserSession

SESSION_TIMEOUT_MINUTES = 30


def create_session(db: Session, user_id: int, username: str, role: str = "cliente") -> str:
    """Crea una nueva sesión persistente y devuelve el token."""
    token = secrets.token_hex(32)
    session = UserSession(
        session_token=token,
        user_id=user_id,
        username=username,
        role=role,
        created_at=datetime.utcnow(),
        last_activity=datetime.utcnow(),
    )
    db.add(session)
    db.commit()
    return token


def get_valid_session(db: Session, token: str):
    """
    Busca la sesión por token y verifica que no haya expirado.
    Devuelve el objeto UserSession si es válido, None si no existe o expiró.
    """
    if not token:
        return None
    # secrets.token_hex(32) = 64 hex chars; reject anything longer to prevent DoS
    if len(token) > 128 or not token.isalnum():
        return None

    session = (
        db.query(UserSession)
        .filter(UserSession.session_token == token)
        .first()
    )
    if not session:
        return None

    cutoff = datetime.utcnow() - timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    if session.last_activity < cutoff:
        # Sesión expirada por inactividad → eliminar
        db.delete(session)
        db.commit()
        return None

    return session


def update_activity(db: Session, token: str) -> None:
    """Actualiza el timestamp de última actividad de la sesión."""
    session = (
        db.query(UserSession)
        .filter(UserSession.session_token == token)
        .first()
    )
    if session:
        session.last_activity = datetime.utcnow()
        db.commit()


def delete_session(db: Session, token: str) -> None:
    """Elimina una sesión (logout)."""
    session = (
        db.query(UserSession)
        .filter(UserSession.session_token == token)
        .first()
    )
    if session:
        db.delete(session)
        db.commit()


def delete_user_sessions(db: Session, user_id: int) -> None:
    """Elimina todas las sesiones de un usuario."""
    db.query(UserSession).filter(UserSession.user_id == user_id).delete()
    db.commit()

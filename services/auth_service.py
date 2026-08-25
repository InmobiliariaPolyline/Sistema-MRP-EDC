import bcrypt
import re
from sqlalchemy.orm import Session
from models.user import User
from models.failed_login import FailedLoginAttempt
from datetime import datetime, timedelta

# Configuración de seguridad
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
MIN_PASSWORD_LENGTH = 8
# Requires: lowercase + uppercase + digit + at least one non-alphanumeric character.
# Does NOT restrict which special characters are allowed (_, -, #, etc. all work).
PASSWORD_REGEX = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z\d\s]).+$'
)
EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)
USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_]{3,20}$')

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False

def validate_email(email: str) -> tuple[bool, str]:
    if not email or len(email) > 255:
        return False, "Email inválido"
    if not EMAIL_REGEX.match(email):
        return False, "Formato de email inválido (ejemplo: usuario@empresa.com)"
    return True, ""

def validate_username(username: str) -> tuple[bool, str]:
    if not username:
        return False, "El usuario es requerido"
    if len(username) < 3:
        return False, "El usuario debe tener al menos 3 caracteres"
    if len(username) > 20:
        return False, "El usuario no puede tener más de 20 caracteres"
    if not USERNAME_REGEX.match(username):
        return False, "El usuario solo puede contener letras, números y guiones bajos"
    return True, ""

def validate_password(password: str) -> tuple[bool, str]:
    if not password:
        return False, "La contraseña es requerida"
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres"
    if len(password) > 128:
        return False, "La contraseña es muy larga (máximo 128 caracteres)"
    if not PASSWORD_REGEX.match(password):
        return False, (
            "La contraseña debe contener al menos: "
            "una mayúscula (A-Z), una minúscula (a-z), "
            "un número (0-9) y un carácter especial (_, @, !, #, etc.)"
        )
    return True, ""

def check_account_locked(db: Session, username: str) -> tuple[bool, str]:
    lockout_time = datetime.utcnow() - timedelta(minutes=LOCKOUT_DURATION_MINUTES)
    # Normalize to lowercase to prevent lockout bypass via case variation
    normalized = username.lower()
    recent_failures = db.query(FailedLoginAttempt).filter(
        FailedLoginAttempt.username == normalized,
        FailedLoginAttempt.attempt_time > lockout_time
    ).count()
    if recent_failures >= MAX_LOGIN_ATTEMPTS:
        return True, (
            f"Cuenta temporalmente bloqueada. "
            f"Demasiados intentos fallidos. "
            f"Intenta de nuevo en {LOCKOUT_DURATION_MINUTES} minutos."
        )
    return False, ""

def log_failed_attempt(db: Session, username: str, reason: str, ip_address: str = None):
    failed_attempt = FailedLoginAttempt(
        username=username.lower(),  # always store normalized
        reason=reason,
        ip_address=ip_address,
        attempt_time=datetime.utcnow()
    )
    db.add(failed_attempt)
    db.commit()

def register_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    password_confirm: str = None,
    role: str = "cliente",
):
    """Registra un nuevo usuario con validación completa."""
    valid_user, user_msg = validate_username(username)
    if not valid_user:
        return False, user_msg

    valid_email, email_msg = validate_email(email)
    if not valid_email:
        return False, email_msg

    valid_pass, pass_msg = validate_password(password)
    if not valid_pass:
        return False, pass_msg

    if password_confirm and password != password_confirm:
        return False, "Las contraseñas no coinciden"

    existing_user = db.query(User).filter(
        (User.username.ilike(username)) | (User.email.ilike(email))
    ).first()

    if existing_user:
        if existing_user.username.lower() == username.lower():
            return False, f"El usuario '{username}' ya está registrado"
        else:
            return False, f"El email '{email}' ya está registrado con otro usuario"

    try:
        password_hash = hash_password(password)
        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return True, "Usuario registrado exitosamente"
    except Exception:
        db.rollback()
        return False, "Error al registrar el usuario. Intenta de nuevo."

def login_user(db: Session, username: str, password: str, ip_address: str = None):
    """Autentica un usuario por nombre de usuario O correo electrónico."""
    if not username or not password:
        return False, None, "Completa todos los campos."
    # Reject oversized inputs before any DB operation
    if len(username) > 255 or len(password) > 256:
        return False, None, "Usuario/correo o contraseña incorrectos"

    is_locked, lock_msg = check_account_locked(db, username)
    if is_locked:
        return False, None, lock_msg

    # Busca por username o por email con el mismo campo de entrada
    user = db.query(User).filter(
        (User.username.ilike(username)) | (User.email.ilike(username))
    ).first()

    if not user:
        log_failed_attempt(db, username, "Usuario no encontrado", ip_address)
        return False, None, "Usuario/correo o contraseña incorrectos"

    if not user.is_active:
        return False, None, "Tu cuenta está deshabilitada. Contacta al administrador."

    if not verify_password(password, user.password_hash):
        log_failed_attempt(db, username, "Contraseña incorrecta", ip_address)
        return False, None, "Usuario/correo o contraseña incorrectos"

    db.query(FailedLoginAttempt).filter(
        FailedLoginAttempt.username == username.lower()
    ).delete()
    db.commit()

    return True, user, "Login exitoso"

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username.ilike(username)).first()

# ── Gestión de usuarios (superadmin) ─────────────────────────────────────────

def superadmin_exists(db: Session) -> bool:
    return db.query(User).filter(User.role == "superadmin").first() is not None

def get_all_clients(db: Session):
    """Retorna todos los usuarios con rol 'cliente'."""
    return db.query(User).filter(User.role == "cliente").order_by(User.created_at.desc()).all()

def set_user_active(db: Session, user_id: int, is_active: bool) -> tuple[bool, str]:
    """Habilita o deshabilita una cuenta de cliente."""
    user = db.query(User).filter(User.id == user_id, User.role == "cliente").first()
    if not user:
        return False, "Usuario no encontrado"
    user.is_active = is_active
    db.commit()
    estado = "habilitado" if is_active else "deshabilitado"
    return True, f"Usuario {estado} correctamente"

def delete_client(db: Session, user_id: int) -> tuple[bool, str]:
    """Elimina permanentemente un usuario cliente."""
    user = db.query(User).filter(User.id == user_id, User.role == "cliente").first()
    if not user:
        return False, "Usuario no encontrado"
    try:
        db.delete(user)
        db.commit()
        return True, "Usuario eliminado correctamente"
    except Exception:
        db.rollback()
        return False, "Error al eliminar el usuario"

def update_client(
    db: Session,
    user_id: int,
    new_username: str = None,
    new_email: str = None,
    new_password: str = None,
) -> tuple[bool, str]:
    """Actualiza las credenciales de un cliente (superadmin)."""
    user = db.query(User).filter(User.id == user_id, User.role == "cliente").first()
    if not user:
        return False, "Usuario no encontrado"

    changed = False

    if new_username and new_username.strip() != user.username:
        valid, msg = validate_username(new_username.strip())
        if not valid:
            return False, msg
        existing = db.query(User).filter(
            User.username.ilike(new_username.strip()), User.id != user_id
        ).first()
        if existing:
            return False, f"El usuario '{new_username}' ya está registrado"
        user.username = new_username.strip()
        changed = True

    if new_email and new_email.strip().lower() != (user.email or "").lower():
        valid, msg = validate_email(new_email.strip())
        if not valid:
            return False, msg
        existing = db.query(User).filter(
            User.email.ilike(new_email.strip()), User.id != user_id
        ).first()
        if existing:
            return False, f"El email '{new_email}' ya está registrado con otro usuario"
        user.email = new_email.strip()
        changed = True

    if new_password:
        valid, msg = validate_password(new_password)
        if not valid:
            return False, msg
        user.password_hash = hash_password(new_password)
        changed = True

    if not changed:
        return False, "No se realizaron cambios en los datos"

    try:
        db.commit()
        return True, "Datos actualizados correctamente"
    except Exception:
        db.rollback()
        return False, "Error al actualizar el usuario. Intenta de nuevo."

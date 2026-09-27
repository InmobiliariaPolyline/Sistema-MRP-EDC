from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import streamlit as st
import os
from dotenv import dotenv_values, load_dotenv

load_dotenv()

_LOCAL_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env.local")
_LOCAL_ENV = dotenv_values(_LOCAL_ENV_PATH) if os.path.isfile(_LOCAL_ENV_PATH) else {}

DATABASE_URL = _LOCAL_ENV.get("DATABASE_URL")
if DATABASE_URL:
    print("[OK] Usando DATABASE_URL desde .env.local")

# Try Streamlit secrets first (only available in Streamlit context)
if not DATABASE_URL:
    try:
        import streamlit as st
        if "DATABASE_URL" in st.secrets:
            DATABASE_URL = st.secrets["DATABASE_URL"]
            print("[OK] Usando DATABASE_URL desde Streamlit Secrets")
    except Exception:
        pass

# Fall back to environment variable
if not DATABASE_URL:
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL:
        print("[OK] Usando DATABASE_URL desde .env")

if not DATABASE_URL:
    raise ValueError("No se encontro DATABASE_URL")

is_sqlite = DATABASE_URL.startswith("sqlite")

if is_sqlite:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        connect_args={"sslmode": "require"} if "postgres" in DATABASE_URL else {},
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

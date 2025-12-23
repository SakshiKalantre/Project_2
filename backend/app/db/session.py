from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

_connect_args = {}
if settings.DATABASE_URL.startswith("postgresql://") or settings.DATABASE_URL.startswith("postgres://"):
    if "sslmode=" not in settings.DATABASE_URL:
        _connect_args = {"sslmode": "require"}
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Import all models so they are registered with Base
# This needs to be done after Base is created
from app import models  # noqa: E402, F401

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

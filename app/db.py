"""Configuración de la base de datos y sesiones de SQLAlchemy."""

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


def get_database_url() -> str:
    """Obtiene la URL de conexión desde DATABASE_URL."""
    url = os.getenv("DATABASE_URL", "sqlite:///labtrack.db")

    if url.startswith("postgres://"):
        return url.replace(
            "postgres://",
            "postgresql+psycopg://",
            1,
        )

    if url.startswith("postgresql://") and "+psycopg" not in url:
        return url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    return url


engine = create_engine(get_database_url())

SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Clase base para los modelos ORM."""

    pass


def get_db() -> Generator[Session, None, None]:
    """Entrega una sesión de BD por request y la cierra al finalizar."""
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
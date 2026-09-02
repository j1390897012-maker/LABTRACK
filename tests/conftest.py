"""Configuración global de pruebas.

Este archivo es cargado automáticamente por pytest.
Proporciona fixtures reutilizables para toda la suite de tests.
"""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base


@pytest.fixture(scope="session")
def test_engine():
    """Crea un engine de SQLite en memoria para pruebas.

    Scope: session (se crea una vez por sesión de pruebas).
    """
    # Usar SQLite en memoria con los mismos parámetros que app.db
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )

    # Crear todas las tablas
    Base.metadata.create_all(engine)

    yield engine

    # Limpiar después de todas las pruebas
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Crea una sesión de base de datos para cada prueba.

    Scope: function (se crea una nueva sesión por cada prueba).
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(
        bind=connection,
        expire_on_commit=False,
    )

    session = SessionLocal()

    yield session

    # Rollback al finalizar la prueba (para aislar cada prueba)
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def db_url_in_memory() -> str:
    """Retorna la URL de SQLite en memoria para pruebas."""
    return "sqlite:///:memory:"


@pytest.fixture
def db_url_postgres() -> str:
    """Retorna una URL de PostgreSQL de prueba."""
    return "postgresql://test_user:test_pass@localhost:5432/test_db"
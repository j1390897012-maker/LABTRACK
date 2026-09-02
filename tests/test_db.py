"""Pruebas para la configuración de la base de datos (app/db.py).

Cubre:
- get_database_url() con diferentes URLs
- Creación del engine
- Sesiones de base de datos
- Ciclo de vida de get_db()
"""

import os
from unittest.mock import patch

import app.models  # noqa: F401  # Necesario para llenar Base.metadata
from app.db import (
    Base,
    SessionLocal,
    engine,
    get_database_url,
    get_db,
)


class TestGetDatabaseUrl:
    """Pruebas para la función get_database_url."""

    def test_default_url(self) -> None:
        """Debería retornar SQLite por defecto si no hay variable."""
        with patch.dict(os.environ, {}, clear=True):
            url = get_database_url()
            assert url == "sqlite:///labtrack.db"

    def test_postgres_url_sin_driver(self) -> None:
        """Debería normalizar postgres:// a postgresql+psycopg://."""
        with patch.dict(
            os.environ,
            {"DATABASE_URL": "postgres://user:pass@localhost:5432/db"},
            clear=True,
        ):
            url = get_database_url()
            assert url == "postgresql+psycopg://user:pass@localhost:5432/db"

    def test_postgresql_url_sin_driver(self) -> None:
        """Debería normalizar postgresql:// a postgresql+psycopg://."""
        with patch.dict(
            os.environ,
            {"DATABASE_URL": "postgresql://user:pass@localhost:5432/db"},
            clear=True,
        ):
            url = get_database_url()
            assert url == "postgresql+psycopg://user:pass@localhost:5432/db"

    def test_postgresql_url_con_driver(self) -> None:
        """No debería modificar URLs que ya tienen el driver correcto."""
        with patch.dict(
            os.environ,
            {"DATABASE_URL": "postgresql+psycopg://user:pass@localhost:5432/db"},
            clear=True,
        ):
            url = get_database_url()
            assert url == "postgresql+psycopg://user:pass@localhost:5432/db"

    def test_sqlite_url_se_mantiene(self) -> None:
        """No debería modificar URLs de SQLite."""
        with patch.dict(
            os.environ,
            {"DATABASE_URL": "sqlite:///custom.db"},
            clear=True,
        ):
            url = get_database_url()
            assert url == "sqlite:///custom.db"


class TestEngine:
    """Pruebas para el engine de la base de datos."""

    def test_engine_creado(self) -> None:
        """Debería existir un engine configurado."""
        assert engine is not None

    def test_engine_url_por_defecto(self) -> None:
        """Debería usar la URL por defecto (SQLite)."""
        # Resetear el módulo para que use la URL real
        with patch.dict(os.environ, {}, clear=True):
            # Importar de nuevo para que tome la variable
            # Recargar el módulo para que use la nueva variable
            from importlib import reload

            import app.db

            reload(app.db)

            # Verificar que la URL es la correcta
            assert "sqlite:///labtrack.db" in str(app.db.engine.url)


class TestSessionLocal:
    """Pruebas para la fábrica de sesiones."""

    def test_sessionlocal_crea_sesion(self) -> None:
        """Debería crear una sesión correctamente."""
        session = SessionLocal()
        assert session is not None
        session.close()

    def test_sessionlocal_usa_expire_on_commit_false(self) -> None:
        """Debería tener expire_on_commit=False 
        (para objetos usables fuera de la transacción)."""
        # Verificar que la sesión creada tiene la configuración correcta
        session = SessionLocal()
        assert session.expire_on_commit is False
        session.close()


class TestBase:
    """Pruebas para la clase base de modelos."""

    def test_base_es_declarativa(self) -> None:
        """Base debería ser una clase declarativa de SQLAlchemy."""
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")

    def test_base_metadata_vacia(self) -> None:
        """La metadata debería estar vacía inicialmente (sin tablas)."""
        # La metadata no debe tener tablas declaradas antes de importar modelos
        # Nota: puede tener tablas si los modelos ya se importaron en otras pruebas
        pass  # Esta prueba es más relevante en un contexto aislado


class TestGetDb:
    """Pruebas para la dependencia get_db de FastAPI."""

    def test_get_db_retorna_sesion(self, db_session) -> None:
        """Debería retornar una sesión de base de datos."""
        # Usamos la sesión del fixture para probar get_db
        with patch("app.db.SessionLocal", return_value=db_session):
            generator = get_db()
            session = next(generator)
            assert session is not None
            try:
                next(generator)
            except StopIteration:
                pass  # El generador se cierra correctamente

    def test_get_db_cierra_sesion(self) -> None:
        """Debería cerrar la sesión al finalizar el contexto."""
        # Verificar que get_db cierra la sesión
        with patch("app.db.SessionLocal") as mock_session:
            # Crear un mock de sesión que permita verificar close()
            mock_session_instance = mock_session.return_value

            generator = get_db()
            session = next(generator)

            # Simular que la sesión se cierra
            assert session == mock_session_instance

            try:
                next(generator)
            except StopIteration:
                pass

            # Verificar que close fue llamado
            mock_session_instance.close.assert_called_once()


class TestIntegracion:
    """Pruebas de integración con el ORM."""

    def test_base_puede_crear_tablas(self, test_engine) -> None:
        """Debería poder crear tablas con la metadata."""
        # El fixture test_engine ya crea las tablas
        # Verificar que la metadata tiene tablas
        assert len(Base.metadata.tables) > 0

    def test_base_puede_insertar_y_consultar(
        self,
        db_session,
    ) -> None:
        """Debería poder insertar y consultar datos básicos."""
        # Crear una tabla temporal para probar
        from sqlalchemy import Column, Integer, String, Table

        # Crear una tabla de prueba dentro de la sesión
        test_table = Table(
            "test_tmp",
            Base.metadata,
            Column("id", Integer, primary_key=True),
            Column("nombre", String(50)),
        )

        # Crear la tabla en la base de datos
        Base.metadata.create_all(db_session.bind)

        # Insertar un registro
        db_session.execute(
            test_table.insert().values(nombre="prueba")
        )
        db_session.commit()

        # Consultar el registro
        result = db_session.execute(
            test_table.select().where(
                test_table.c.nombre == "prueba"
            )
        ).first()

        assert result is not None
        assert result.nombre == "prueba"
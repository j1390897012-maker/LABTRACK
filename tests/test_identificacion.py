"""Pruebas para el servicio de identificación RFID (US-09 y US-02)."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_db
from app.main import app
from app.models import Estudiante
from app.models.labtrack import Sesion
from app.schemas.identificacion import AsignacionRFIDRequest
from app.services.identificaciones import IdentificacionService

client = TestClient(app)

@pytest.fixture
def estudiante_con_rfid(db_session: Session) -> Estudiante:
    """Crea un estudiante con RFID asignado."""
    estudiante = Estudiante(
        nombre="Juan Pérez",
        matricula="A12345",
        uid_rfid="RFID-001",
    )
    db_session.add(estudiante)
    db_session.commit()
    db_session.refresh(estudiante)
    return estudiante


@pytest.fixture
def estudiante_sin_rfid(db_session: Session) -> Estudiante:
    """Crea un estudiante sin RFID asignado."""
    estudiante = Estudiante(
        nombre="María López",
        matricula="B67890",
        uid_rfid=None,
    )
    db_session.add(estudiante)
    db_session.commit()
    db_session.refresh(estudiante)
    return estudiante


class TestEnrolamientoRFID:
    """Pruebas para el enrolamiento de RFID (US-09)."""

    def test_enrolar_rfid_exitoso(
        self,
        db_session: Session,
        estudiante_sin_rfid: Estudiante,
    ) -> None:
        """Debería asignar el RFID correctamente."""
        service = IdentificacionService()

        request = AsignacionRFIDRequest(
            tipo="rfid",
            valor="RFID-002",
            matricula=estudiante_sin_rfid.matricula,
        )

        response = service.enrolar_rfid(db_session, request)

        assert response.estudiante_id == estudiante_sin_rfid.id
        assert response.nombre == "María López"
        assert response.matricula == "B67890"
        assert response.uid_rfid == "RFID-002"
        assert "exitosamente" in response.mensaje

    def test_enrolar_rfid_estudiante_inexistente(
        self,
        db_session: Session,
    ) -> None:
        """Debería lanzar error 404 si el estudiante no existe."""
        service = IdentificacionService()

        request = AsignacionRFIDRequest(
            tipo="rfid",
            valor="RFID-003",
            matricula="MATRICULA-INEXISTENTE",
        )

        with pytest.raises(HTTPException) as exc_info:
            service.enrolar_rfid(db_session, request)

        assert exc_info.value.status_code == 404

    def test_enrolar_rfid_ya_asignado(
        self,
        db_session: Session,
        estudiante_con_rfid: Estudiante,
    ) -> None:
        """Debería lanzar error 409 si el RFID ya está asignado a otro estudiante."""
        service = IdentificacionService()

        estudiante = Estudiante(
            nombre="Carlos Ruiz",
            matricula="C11223",
            uid_rfid=None,
        )

        db_session.add(estudiante)
        db_session.commit()
        db_session.refresh(estudiante)

        request = AsignacionRFIDRequest(
            tipo="rfid",
            valor="RFID-001",
            matricula=estudiante.matricula,
        )

        with pytest.raises(HTTPException) as exc_info:
            service.enrolar_rfid(db_session, request)

        assert exc_info.value.status_code == 409


class TestEscaneoRFID:
    """Pruebas para el escaneo de RFID y control de sesiones (US-02)."""

    def test_escanear_rfid_estudiante_nuevo_crea_sesion(self, db_session):
        # 1. Asegurar que apunte a la base de datos de pruebas
        app.dependency_overrides[get_db] = lambda: db_session
        
        # 2. Primero, enrolamos un estudiante para la prueba
        client.post(
            "/api/estudiantes",
            json={"nombre": "Alexander Torres Andrade", "matricula": "S23013956"}
        )
        client.post(
            "/api/identificaciones/enrolar",
            json={"tipo": "rfid", "valor": "TAG-123", "matricula": "S23013956"}
        )
        
        # 3. El ESP32 escanea la tarjeta
        response = client.post(
            "/api/identificaciones/scan",
            json={"tipo": "rfid", "valor": "TAG-123", "lector_id": "esp32-mesa-1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["estado"] == "registrado"
        assert data["accion"] == "sesion_abierta"
        assert data["sesion_id"] is not None
        
        app.dependency_overrides.clear()

    def test_escanear_rfid_estudiante_con_sesion_continua_sesion(
        self, db_session
        ):
        app.dependency_overrides[get_db] = lambda: db_session
        
        # Insertamos el registro directamente con SQLAlchemy para simular el estado
        estudiante = Estudiante(nombre="Alex", matricula="TEST-1", uid_rfid="TAG-456")
        db_session.add(estudiante)
        db_session.commit()
        
        sesion = Sesion(estudiante_id=estudiante.id, estado="abierta")
        db_session.add(sesion)
        db_session.commit()
        
        response = client.post(
            "/api/identificaciones/scan",
            json={"tipo": "rfid", "valor": "TAG-456", "lector_id": "esp32-mesa-1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["accion"] == "sesion_continuada"
        assert data["sesion_id"] == sesion.id
        
        app.dependency_overrides.clear()
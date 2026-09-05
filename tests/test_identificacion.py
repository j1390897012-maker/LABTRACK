"""Pruebas para el servicio de identificación RFID (US-09)."""

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Estudiante
from app.schemas.identificacion import AsignacionRFIDRequest
from app.services.identificaciones import IdentificacionService


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
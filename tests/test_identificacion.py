"""Pruebas para el servicio de identificación RFID y QR (US-09, US-02, US-03)."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_db
from app.main import app
from app.models.labtrack import Equipo, Estudiante, Sesion, TipoAccesorio, TipoEquipo
from app.repositories.sesion_repository import SesionRepository
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
        
        sesion = Sesion(estudiante_id=estudiante.id, estado="Activa")
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


class TestEscaneoQR:
    """Pruebas del flujo integrado US-06 y US-03."""

    def test_flujo_completo_identificacion_y_qr(self, db_session):
        app.dependency_overrides[get_db] = lambda: db_session

        # 1. Preparar datos simulados en la base de datos de pruebas
        tipo = TipoEquipo(nombre="Osciloscopio")
        db_session.add(tipo)
        db_session.commit()

        acc = TipoAccesorio(
            nombre="Puntas",
            tipo_equipo_id=tipo.id,
            cantidad_default=2,
        )
        db_session.add(acc)

        equipo = Equipo(
            codigo="OSC-0397",
            tipo_equipo_id=tipo.id,
            estado="Disponible",
        )
        db_session.add(equipo)

        estudiante = Estudiante(
            nombre="Alberto",
            matricula="S12345",
            uid_rfid="A1-B2-C3-D4",
        )
        db_session.add(estudiante)
        db_session.commit()

        # 2. US-02: Simular escaneo de tarjeta RFID
        res_rfid = client.post(
            "/api/identificaciones/scan",
            json={
                "tipo": "rfid",
                "valor": "A1-B2-C3-D4",
            },
        )

        assert res_rfid.status_code == 200

        datos_rfid = res_rfid.json()

        sesion_id = datos_rfid["sesion_id"]

        assert sesion_id is not None
        assert datos_rfid["accion"] == "sesion_abierta"

        # 3. US-06: Simular escaneo de QR y obtener decisión
        res_qr = client.post(
            "/api/identificaciones/scan",
            json={
                "tipo": "qr",
                "valor": "OSC-0397",
                
            },
        )

        assert res_qr.status_code == 200

        datos_qr = res_qr.json()

        assert datos_qr["codigo"] == "OSC-0397"
        assert datos_qr["estado"] == "Disponible"
        assert datos_qr["accion"] == "confirmar_prestamo"

        assert len(datos_qr["estudiantes"]) == 1
        assert datos_qr["estudiantes"][0]["matricula"] == "S12345"

        # 4. US-03: Confirmar el préstamo y ejecutar la operación
        repo_sesion = SesionRepository()

        prestamo = repo_sesion.add_equipo(
            db_session,
            sesion_id,
            equipo,
        )

        assert prestamo.sesion_id == sesion_id
        assert prestamo.equipo_id == equipo.id
        assert prestamo.estado == "Prestado"

        db_session.refresh(equipo)

        assert equipo.estado == "Prestado"

        app.dependency_overrides.clear()
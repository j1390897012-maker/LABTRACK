"""Pruebas para el registro manual de respaldo (US-12)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_db
from app.main import app
from app.models.labtrack import Equipo, Estudiante, Sesion, SesionEquipo, TipoEquipo

client = TestClient(app)


def _crear_estudiante(db_session: Session, matricula: str = "S555666") -> Estudiante:
    estudiante = Estudiante(nombre="Alberto", matricula=matricula)
    db_session.add(estudiante)
    db_session.commit()
    return estudiante


def _crear_equipo(
    db_session: Session, codigo: str = "OSC-0500", estado: str = "Disponible"
) -> Equipo:
    tipo = TipoEquipo(nombre=f"Tipo-{codigo}")
    db_session.add(tipo)
    db_session.commit()

    equipo = Equipo(codigo=codigo, tipo_equipo_id=tipo.id, estado=estado)
    db_session.add(equipo)
    db_session.commit()
    return equipo


# --- Escenario: Registrar préstamo manual --------------------------------


def test_abrir_sesion_manual_crea_sesion(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    estudiante = _crear_estudiante(db_session)

    response = client.post(
        "/api/sesiones", json={"estudiante_id": estudiante.id}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["estudiante_id"] == estudiante.id
    assert data["estado"] == "Activa"


def test_abrir_sesion_manual_reutiliza_sesion_activa(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    estudiante = _crear_estudiante(db_session)
    sesion_previa = Sesion(estudiante_id=estudiante.id, estado="Activa")
    db_session.add(sesion_previa)
    db_session.commit()

    response = client.post(
        "/api/sesiones", json={"estudiante_id": estudiante.id}
    )

    assert response.status_code == 201
    assert response.json()["sesion_id"] == sesion_previa.id


def test_abrir_sesion_manual_estudiante_inexistente_404(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    response = client.post("/api/sesiones", json={"estudiante_id": 99999})

    assert response.status_code == 404


def test_agregar_equipo_manual_procesa_prestamo(db_session: Session):
    """Given estudiante y equipo seleccionados manualmente, se procesa el
    préstamo con la misma lógica del flujo normal."""
    app.dependency_overrides[get_db] = lambda: db_session
    estudiante = _crear_estudiante(db_session)
    equipo = _crear_equipo(db_session)
    sesion = Sesion(estudiante_id=estudiante.id, estado="Activa")
    db_session.add(sesion)
    db_session.commit()

    response = client.post(
        f"/api/sesiones/{sesion.id}/equipos",
        json={"equipo_id": equipo.id},
    )

    assert response.status_code == 200
    db_session.refresh(equipo)
    assert equipo.estado == "Prestado"


def test_agregar_equipo_manual_sin_equipo_muestra_mensaje(db_session: Session):
    """Escenario: Intentar registro manual con datos incompletos."""
    app.dependency_overrides[get_db] = lambda: db_session
    estudiante = _crear_estudiante(db_session)
    sesion = Sesion(estudiante_id=estudiante.id, estado="Activa")
    db_session.add(sesion)
    db_session.commit()

    response = client.post(
        f"/api/sesiones/{sesion.id}/equipos",
        json={},
    )

    assert response.status_code == 400
    assert "seleccionar un equipo" in response.json()["detail"].lower()


def test_agregar_equipo_manual_equipo_no_disponible_409(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    estudiante = _crear_estudiante(db_session)
    equipo = _crear_equipo(db_session, estado="Prestado")
    sesion = Sesion(estudiante_id=estudiante.id, estado="Activa")
    db_session.add(sesion)
    db_session.commit()

    response = client.post(
        f"/api/sesiones/{sesion.id}/equipos",
        json={"equipo_id": equipo.id},
    )

    assert response.status_code == 409


# --- Escenario: Iniciar devolución manual (POST /api/devoluciones) -------


def test_iniciar_devolucion_manual_exitosa(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    estudiante = _crear_estudiante(db_session)
    equipo = _crear_equipo(db_session, estado="Prestado")
    sesion = Sesion(estudiante_id=estudiante.id, estado="Activa")
    db_session.add(sesion)
    db_session.commit()
    sesion_equipo = SesionEquipo(
        sesion_id=sesion.id, equipo_id=equipo.id, estado="Prestado"
    )
    db_session.add(sesion_equipo)
    db_session.commit()

    response = client.post(
        "/api/devoluciones", json={"equipo_id": equipo.id}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["sesion_equipo_id"] == sesion_equipo.id
    assert data["estudiante_id"] == estudiante.id


def test_iniciar_devolucion_manual_sin_equipo_400(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    response = client.post("/api/devoluciones", json={})

    assert response.status_code == 400


def test_iniciar_devolucion_manual_equipo_disponible_409(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    equipo = _crear_equipo(db_session, estado="Disponible")

    response = client.post(
        "/api/devoluciones", json={"equipo_id": equipo.id}
    )

    assert response.status_code == 409

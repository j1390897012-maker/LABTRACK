"""Pruebas para el registro de fallas al devolver un equipo (US-08)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_db
from app.main import app
from app.models.labtrack import (
    Equipo,
    Estudiante,
    Falla,
    Sesion,
    SesionEquipo,
    TipoEquipo,
)

client = TestClient(app)


def _crear_prestamo_en_curso(db_session: Session) -> SesionEquipo:
    """Helper: crea equipo prestado + sesión + sesion_equipo listos para devolver."""
    tipo = TipoEquipo(nombre="Osciloscopio")
    db_session.add(tipo)
    db_session.commit()

    equipo = Equipo(codigo="OSC-0307", tipo_equipo_id=tipo.id, estado="Prestado")
    db_session.add(equipo)

    estudiante = Estudiante(nombre="Alberto", matricula="S333444")
    db_session.add(estudiante)
    db_session.commit()

    sesion = Sesion(estudiante_id=estudiante.id, estado="Activa")
    db_session.add(sesion)
    db_session.commit()

    sesion_equipo = SesionEquipo(
        sesion_id=sesion.id, equipo_id=equipo.id, estado="Prestado"
    )
    db_session.add(sesion_equipo)
    db_session.commit()

    return sesion_equipo


def test_registrar_falla_marca_equipo_en_revision(db_session: Session):
    """Escenario: Registrar una falla."""
    app.dependency_overrides[get_db] = lambda: db_session

    sesion_equipo = _crear_prestamo_en_curso(db_session)

    response = client.patch(
        f"/api/devoluciones/{sesion_equipo.id}/falla",
        json={
            "hubo_falla": True,
            "descripcion": "Falso contacto en canal 1",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["equipo_estado"] == "En revisión"
    assert data["falla_id"] is not None

    equipo = db_session.get(Equipo, sesion_equipo.equipo_id)
    db_session.refresh(equipo)
    assert equipo.estado == "En revisión"

    falla = db_session.get(Falla, data["falla_id"])
    assert falla is not None
    assert falla.descripcion == "Falso contacto en canal 1"
    assert falla.estado == "Pendiente"
    assert falla.equipo_id == equipo.id


def test_devolucion_sin_fallas_marca_equipo_disponible(db_session: Session):
    """Escenario: Devolución sin fallas."""
    app.dependency_overrides[get_db] = lambda: db_session

    sesion_equipo = _crear_prestamo_en_curso(db_session)

    response = client.patch(
        f"/api/devoluciones/{sesion_equipo.id}/falla",
        json={"hubo_falla": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["equipo_estado"] == "Disponible"
    assert data["falla_id"] is None

    equipo = db_session.get(Equipo, sesion_equipo.equipo_id)
    db_session.refresh(equipo)
    assert equipo.estado == "Disponible"


def test_registrar_falla_sin_descripcion_falla_validacion(db_session: Session):
    """hubo_falla=True sin descripción debe rechazarse (422)."""
    app.dependency_overrides[get_db] = lambda: db_session

    sesion_equipo = _crear_prestamo_en_curso(db_session)

    response = client.patch(
        f"/api/devoluciones/{sesion_equipo.id}/falla",
        json={"hubo_falla": True},
    )

    assert response.status_code == 422


def test_registrar_falla_prestamo_inexistente_devuelve_404(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    response = client.patch(
        "/api/devoluciones/99999/falla",
        json={"hubo_falla": False},
    )

    assert response.status_code == 404


def test_fallas_anteriores_no_se_sobrescriben(db_session: Session):
    """Dos fallas registradas en devoluciones distintas deben coexistir."""
    app.dependency_overrides[get_db] = lambda: db_session

    sesion_equipo = _crear_prestamo_en_curso(db_session)

    client.patch(
        f"/api/devoluciones/{sesion_equipo.id}/falla",
        json={"hubo_falla": True, "descripcion": "Falla 1"},
    )
    client.patch(
        f"/api/devoluciones/{sesion_equipo.id}/falla",
        json={"hubo_falla": True, "descripcion": "Falla 2"},
    )

    equipo_id = sesion_equipo.equipo_id
    fallas = (
        db_session.query(Falla).filter(Falla.equipo_id == equipo_id).all()
    )
    assert len(fallas) == 2

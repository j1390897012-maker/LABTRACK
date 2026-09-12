"""Pruebas para la consulta de fallas (GET /api/fallas, GET /api/fallas/{id})."""

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


def _crear_falla_con_devolucion(db_session: Session) -> Falla:
    """Crea una falla asociada a un préstamo (equipo + estudiante conocidos)."""
    tipo = TipoEquipo(nombre="Osciloscopio")
    db_session.add(tipo)
    db_session.commit()

    equipo = Equipo(codigo="OSC-0900", tipo_equipo_id=tipo.id, estado="En revisión")
    db_session.add(equipo)

    estudiante = Estudiante(nombre="Beto Salinas", matricula="S21099001")
    db_session.add(estudiante)
    db_session.commit()

    sesion = Sesion(estudiante_id=estudiante.id, estado="Activa")
    db_session.add(sesion)
    db_session.commit()

    sesion_equipo = SesionEquipo(
        sesion_id=sesion.id, equipo_id=equipo.id, estado="Devuelto"
    )
    db_session.add(sesion_equipo)
    db_session.commit()

    falla = Falla(
        equipo_id=equipo.id,
        sesion_equipo_id=sesion_equipo.id,
        descripcion="Pantalla no enciende",
        estado="Pendiente",
    )
    db_session.add(falla)
    db_session.commit()
    db_session.refresh(falla)
    return falla


def test_listar_fallas(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    falla = _crear_falla_con_devolucion(db_session)

    response = client.get("/api/fallas")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    item = data[0]
    assert item["id"] == falla.id
    assert item["codigo_equipo"] == "OSC-0900"
    assert item["tipo_equipo"] == "Osciloscopio"
    assert item["matricula"] == "S21099001"
    assert item["estudiante_nombre"] == "Beto Salinas"
    assert item["estado"] == "Pendiente"

    app.dependency_overrides.clear()


def test_filtrar_fallas_por_estado_pendiente(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    tipo = TipoEquipo(nombre="Multímetro")
    db_session.add(tipo)
    db_session.commit()

    equipo = Equipo(codigo="MULT-900", tipo_equipo_id=tipo.id, estado="Disponible")
    db_session.add(equipo)
    db_session.commit()

    falla_pendiente = Falla(
        equipo_id=equipo.id,
        sesion_equipo_id=None,
        descripcion="No enciende",
        estado="Pendiente",
    )
    falla_resuelta = Falla(
        equipo_id=equipo.id,
        sesion_equipo_id=None,
        descripcion="Cable dañado",
        estado="Resuelta",
    )
    db_session.add_all([falla_pendiente, falla_resuelta])
    db_session.commit()

    response = client.get("/api/fallas", params={"estado": "Pendiente"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["descripcion"] == "No enciende"

    app.dependency_overrides.clear()


def test_falla_sin_devolucion_no_tiene_matricula(db_session: Session):
    """Una falla registrada por cambio de estado manual (sin sesion_equipo)
    no debe traer matrícula ni nombre de estudiante."""
    app.dependency_overrides[get_db] = lambda: db_session

    tipo = TipoEquipo(nombre="Fuente")
    db_session.add(tipo)
    db_session.commit()

    equipo = Equipo(codigo="FUE-900", tipo_equipo_id=tipo.id, estado="En revisión")
    db_session.add(equipo)
    db_session.commit()

    falla = Falla(
        equipo_id=equipo.id,
        sesion_equipo_id=None,
        descripcion="Fusible quemado",
        estado="Pendiente",
    )
    db_session.add(falla)
    db_session.commit()

    response = client.get("/api/fallas")

    assert response.status_code == 200
    data = response.json()
    assert data[0]["matricula"] is None
    assert data[0]["estudiante_nombre"] is None

    app.dependency_overrides.clear()


def test_detalle_falla(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    falla = _crear_falla_con_devolucion(db_session)

    response = client.get(f"/api/fallas/{falla.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == falla.id
    assert data["codigo_equipo"] == "OSC-0900"
    assert data["matricula"] == "S21099001"

    app.dependency_overrides.clear()


def test_detalle_falla_inexistente_404(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    response = client.get("/api/fallas/99999")

    assert response.status_code == 404

    app.dependency_overrides.clear()

"""Pruebas para GET /api/equipos, GET /api/equipos/{codigo} y
GET /api/equipos/{codigo}/historial (US-10)."""

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


def test_listar_equipos(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    tipo = TipoEquipo(nombre="Osciloscopio")
    db_session.add(tipo)
    db_session.commit()

    db_session.add_all(
        [
            Equipo(codigo="OSC-0307", tipo_equipo_id=tipo.id, estado="Disponible"),
            Equipo(codigo="OSC-0308", tipo_equipo_id=tipo.id, estado="Prestado"),
        ]
    )
    db_session.commit()

    response = client.get("/api/equipos")

    assert response.status_code == 200
    codigos = {e["codigo"] for e in response.json()}
    assert {"OSC-0307", "OSC-0308"}.issubset(codigos)

    app.dependency_overrides.clear()


def test_buscar_equipo_por_codigo_parcial(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    tipo = TipoEquipo(nombre="Multímetro")
    db_session.add(tipo)
    db_session.commit()

    db_session.add(
        Equipo(codigo="MULT-001", tipo_equipo_id=tipo.id, estado="Disponible")
    )
    db_session.commit()

    response = client.get("/api/equipos", params={"codigo": "MULT"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["codigo"] == "MULT-001"
    assert data[0]["estado"] == "Disponible"
    assert data[0]["tipo"] == "Multímetro"

    app.dependency_overrides.clear()


def test_filtrar_equipos_por_estado(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    tipo = TipoEquipo(nombre="Cautín")
    db_session.add(tipo)
    db_session.commit()

    db_session.add_all(
        [
            Equipo(codigo="CAU-001", tipo_equipo_id=tipo.id, estado="Disponible"),
            Equipo(codigo="CAU-002", tipo_equipo_id=tipo.id, estado="En revisión"),
        ]
    )
    db_session.commit()

    response = client.get("/api/equipos", params={"estado": "En revisión"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["codigo"] == "CAU-002"

    app.dependency_overrides.clear()


def test_detalle_equipo_disponible(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    tipo = TipoEquipo(nombre="Fuente")
    db_session.add(tipo)
    db_session.commit()

    db_session.add(
        Equipo(codigo="FUE-100", tipo_equipo_id=tipo.id, estado="Disponible")
    )
    db_session.commit()

    response = client.get("/api/equipos/FUE-100")

    assert response.status_code == 200
    data = response.json()
    assert data["codigo"] == "FUE-100"
    assert data["estado"] == "Disponible"
    assert data["prestamo_activo"] is None
    assert data["fallas"] == []

    app.dependency_overrides.clear()


def test_detalle_equipo_prestado_incluye_prestamo_activo(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    tipo = TipoEquipo(nombre="Osciloscopio")
    db_session.add(tipo)
    db_session.commit()

    equipo = Equipo(codigo="OSC-0500", tipo_equipo_id=tipo.id, estado="Prestado")
    db_session.add(equipo)

    estudiante = Estudiante(nombre="Alejandro Ruiz", matricula="S21055555")
    db_session.add(estudiante)
    db_session.commit()

    sesion = Sesion(estudiante_id=estudiante.id, estado="Activa")
    db_session.add(sesion)
    db_session.commit()

    prestamo = SesionEquipo(sesion_id=sesion.id, equipo_id=equipo.id, estado="Prestado")
    db_session.add(prestamo)
    db_session.commit()

    response = client.get("/api/equipos/OSC-0500")

    assert response.status_code == 200
    data = response.json()
    assert data["prestamo_activo"]["matricula"] == "S21055555"
    assert data["prestamo_activo"]["estudiante_nombre"] == "Alejandro Ruiz"

    app.dependency_overrides.clear()


def test_detalle_equipo_inexistente_404(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    response = client.get("/api/equipos/NO-EXISTE")

    assert response.status_code == 404

    app.dependency_overrides.clear()


def test_historial_equipo_inexistente_404(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    response = client.get("/api/equipos/NO-EXISTE/historial")

    assert response.status_code == 404

    app.dependency_overrides.clear()


def test_historial_equipo_ordenado_por_fecha_descendente(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    tipo = TipoEquipo(nombre="Osciloscopio")
    db_session.add(tipo)
    db_session.commit()

    equipo = Equipo(codigo="OSC-0307", tipo_equipo_id=tipo.id, estado="Disponible")
    db_session.add(equipo)

    est1 = Estudiante(nombre="Primero", matricula="S21000001")
    est2 = Estudiante(nombre="Segundo", matricula="S21000002")
    db_session.add_all([est1, est2])
    db_session.commit()

    sesion1 = Sesion(estudiante_id=est1.id, estado="Cerrada")
    sesion2 = Sesion(estudiante_id=est2.id, estado="Activa")
    db_session.add_all([sesion1, sesion2])
    db_session.commit()

    from datetime import datetime

    prestamo_antiguo = SesionEquipo(
        sesion_id=sesion1.id,
        equipo_id=equipo.id,
        estado="Devuelto",
        fecha_prestamo=datetime(2026, 1, 1),
        fecha_devolucion=datetime(2026, 1, 2),
    )
    prestamo_reciente = SesionEquipo(
        sesion_id=sesion2.id,
        equipo_id=equipo.id,
        estado="Prestado",
        fecha_prestamo=datetime(2026, 6, 1),
    )
    db_session.add_all([prestamo_antiguo, prestamo_reciente])
    db_session.commit()

    falla = Falla(
        equipo_id=equipo.id,
        sesion_equipo_id=prestamo_antiguo.id,
        descripcion="Pantalla parpadea",
        estado="Pendiente",
    )
    db_session.add(falla)
    db_session.commit()

    response = client.get("/api/equipos/OSC-0307/historial")

    assert response.status_code == 200
    data = response.json()
    assert data["codigo"] == "OSC-0307"
    assert len(data["prestamos"]) == 2
    # Más reciente primero
    assert data["prestamos"][0]["matricula"] == "S21000002"
    assert data["prestamos"][1]["matricula"] == "S21000001"
    assert len(data["prestamos"][1]["fallas"]) == 1

    app.dependency_overrides.clear()

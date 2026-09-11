"""Pruebas para GET /api/sesiones/activa?matricula=..."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_db
from app.main import app
from app.models.labtrack import Equipo, Estudiante, Sesion, SesionEquipo, TipoEquipo

client = TestClient(app)


def test_sesion_activa_por_matricula_con_equipos(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    tipo = TipoEquipo(nombre="Osciloscopio")
    db_session.add(tipo)
    db_session.commit()

    equipo = Equipo(codigo="OSC-0307", tipo_equipo_id=tipo.id, estado="Prestado")
    db_session.add(equipo)

    estudiante = Estudiante(nombre="Alejandro Ruiz", matricula="S21077777")
    db_session.add(estudiante)
    db_session.commit()

    sesion = Sesion(estudiante_id=estudiante.id, estado="Activa")
    db_session.add(sesion)
    db_session.commit()

    prestamo = SesionEquipo(sesion_id=sesion.id, equipo_id=equipo.id, estado="Prestado")
    db_session.add(prestamo)
    db_session.commit()

    response = client.get("/api/sesiones/activa", params={"matricula": "S21077777"})

    assert response.status_code == 200
    data = response.json()
    assert data["matricula"] == "S21077777"
    assert data["estado"] == "Activa"
    assert len(data["equipos"]) == 1
    assert data["equipos"][0]["codigo"] == "OSC-0307"

    app.dependency_overrides.clear()


def test_sesion_activa_estudiante_inexistente_404(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    response = client.get("/api/sesiones/activa", params={"matricula": "NO-EXISTE"})

    assert response.status_code == 404

    app.dependency_overrides.clear()


def test_sesion_activa_sin_sesion_abierta_404(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    estudiante = Estudiante(nombre="Sin Sesion", matricula="S21088888")
    db_session.add(estudiante)
    db_session.commit()

    response = client.get("/api/sesiones/activa", params={"matricula": "S21088888"})

    assert response.status_code == 404

    app.dependency_overrides.clear()

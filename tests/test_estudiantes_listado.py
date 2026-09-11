"""Pruebas para el listado y búsqueda de estudiantes (GET /api/estudiantes)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_db
from app.main import app
from app.models.labtrack import Estudiante

client = TestClient(app)


def test_listar_estudiantes(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    db_session.add_all(
        [
            Estudiante(nombre="Ana Torres", matricula="S21012345"),
            Estudiante(nombre="Luis Pérez", matricula="S21099999"),
        ]
    )
    db_session.commit()

    response = client.get("/api/estudiantes")

    assert response.status_code == 200
    matriculas = {e["matricula"] for e in response.json()}
    assert {"S21012345", "S21099999"}.issubset(matriculas)

    app.dependency_overrides.clear()


def test_buscar_estudiante_por_matricula(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    db_session.add_all(
        [
            Estudiante(nombre="Ana Torres", matricula="S21012345"),
            Estudiante(nombre="Luis Pérez", matricula="S21099999"),
        ]
    )
    db_session.commit()

    response = client.get("/api/estudiantes", params={"matricula": "S21012345"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["matricula"] == "S21012345"
    assert data[0]["nombre"] == "Ana Torres"

    app.dependency_overrides.clear()


def test_buscar_estudiante_por_nombre_parcial(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    db_session.add_all(
        [
            Estudiante(nombre="Ana Torres", matricula="S21012345"),
            Estudiante(nombre="Luis Pérez", matricula="S21099999"),
        ]
    )
    db_session.commit()

    response = client.get("/api/estudiantes", params={"nombre": "torres"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["matricula"] == "S21012345"

    app.dependency_overrides.clear()


def test_buscar_estudiante_sin_resultados(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    response = client.get("/api/estudiantes", params={"matricula": "NO-EXISTE"})

    assert response.status_code == 200
    assert response.json() == []

    app.dependency_overrides.clear()

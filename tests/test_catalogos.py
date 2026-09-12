"""Pruebas para los catálogos (GET /api/tipos-equipo, GET /api/tipos-accesorio)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_db
from app.main import app
from app.models.labtrack import TipoAccesorio, TipoEquipo

client = TestClient(app)


def test_listar_tipos_equipo(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    db_session.add_all(
        [TipoEquipo(nombre="Osciloscopio"), TipoEquipo(nombre="Multímetro")]
    )
    db_session.commit()

    response = client.get("/api/tipos-equipo")

    assert response.status_code == 200
    nombres = {t["nombre"] for t in response.json()}
    assert {"Osciloscopio", "Multímetro"}.issubset(nombres)

    app.dependency_overrides.clear()


def test_listar_tipos_accesorio_filtrado_por_tipo_equipo(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    tipo1 = TipoEquipo(nombre="Osciloscopio")
    tipo2 = TipoEquipo(nombre="Multímetro")
    db_session.add_all([tipo1, tipo2])
    db_session.commit()

    db_session.add_all(
        [
            TipoAccesorio(nombre="Puntas", tipo_equipo_id=tipo1.id, cantidad_default=2),
            TipoAccesorio(nombre="Cables", tipo_equipo_id=tipo2.id, cantidad_default=1),
        ]
    )
    db_session.commit()

    response = client.get("/api/tipos-accesorio", params={"tipo_equipo_id": tipo1.id})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["nombre"] == "Puntas"

    app.dependency_overrides.clear()

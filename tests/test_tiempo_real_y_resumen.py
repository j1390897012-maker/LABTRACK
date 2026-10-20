"""Resumen por estado, registro con datos de inventario y WebSocket."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_db
from app.main import app
from app.models.labtrack import Equipo, TipoEquipo

client = TestClient(app)


def _equipos(db: Session, estados: list[str]) -> None:
    tipo = TipoEquipo(nombre="Fuente")
    db.add(tipo)
    db.flush()
    for i, estado in enumerate(estados):
        db.add(Equipo(codigo=f"F{i}", tipo_equipo_id=tipo.id, estado=estado))
    db.commit()


def test_resumen_cuenta_cada_equipo_una_sola_vez(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    _equipos(
        db_session,
        ["Disponible", "Disponible", "Prestado", "En revisión", "Baja", "Raro"],
    )
    r = client.get("/api/equipos/resumen")
    assert r.status_code == 200
    d = r.json()
    assert d == {
        "total": 6,
        "disponibles": 2,
        "prestados": 1,
        "en_revision": 1,
        "baja": 1,
        "otros": 1,
    }
    assert d["total"] == sum(v for k, v in d.items() if k != "total")
    assert d["total"] == len(client.get("/api/equipos").json())
    app.dependency_overrides.clear()


def test_resumen_vacio(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    assert client.get("/api/equipos/resumen").json()["total"] == 0
    app.dependency_overrides.clear()


def test_registrar_con_datos_de_inventario(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    r = client.post(
        "/api/equipos",
        json={
            "codigo": " 18 ",
            "tipo": "Fuente de alimentación",
            "numero_inventario": "N00122321",
            "marca": "BK Precision",
            "modelo": "",
        },
    )
    assert r.status_code == 201
    d = r.json()
    assert d["codigo"] == "18" and d["numero_inventario"] == "N00122321"
    assert d["marca"] == "BK Precision" and d["modelo"] is None
    det = client.get("/api/equipos/18").json()
    assert det["numero_inventario"] == "N00122321"

    # El inventario oficial no se puede repetir en otro equipo
    r = client.post(
        "/api/equipos",
        json={"codigo": "19", "tipo": "Fuente", "numero_inventario": "N00122321"},
    )
    assert r.status_code == 409 and "18" in r.json()["detail"]
    # Código vacío rechazado
    r = client.post("/api/equipos", json={"codigo": "  ", "tipo": "Fuente"})
    assert r.status_code == 422
    app.dependency_overrides.clear()


def test_websocket_avisa_de_cambios(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    with client.websocket_connect("/ws") as ws:
        ws.send_text("ping")
        assert ws.receive_text() == "pong"

        client.post("/api/equipos", json={"codigo": "X1", "tipo": "Fuente"})
        msg = ws.receive_json()
        assert msg["evento"] == "cambio" and msg["recurso"] == "equipos"
        assert msg["metodo"] == "POST"

        # Un rechazo (409) no genera aviso; el siguiente éxito sí
        client.post("/api/equipos", json={"codigo": "X1", "tipo": "Fuente"})
        client.post("/api/equipos", json={"codigo": "X2", "tipo": "Fuente"})
        assert ws.receive_json()["ruta"] == "/api/equipos"
        assert client.get("/api/equipos/resumen").status_code == 200
    app.dependency_overrides.clear()

"""Pruebas para el cambio manual de estado de un equipo
(PATCH /api/equipos/{codigo}/estado)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_db
from app.main import app
from app.models.labtrack import Equipo, Falla, TipoEquipo

client = TestClient(app)


def _crear_equipo(
    db_session: Session, codigo: str, estado: str = "Disponible"
) -> Equipo:
    tipo = TipoEquipo(nombre=f"Tipo-{codigo}")
    db_session.add(tipo)
    db_session.commit()

    equipo = Equipo(codigo=codigo, tipo_equipo_id=tipo.id, estado=estado)
    db_session.add(equipo)
    db_session.commit()
    return equipo


def test_cambiar_estado_sin_falla_queda_disponible(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    equipo = _crear_equipo(db_session, "OSC-0700", estado="En revisión")

    response = client.patch(
        f"/api/equipos/{equipo.codigo}/estado",
        json={"hubo_falla": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["codigo"] == "OSC-0700"
    assert data["estado"] == "Disponible"
    assert data["falla_id"] is None

    db_session.refresh(equipo)
    assert equipo.estado == "Disponible"

    app.dependency_overrides.clear()


def test_cambiar_estado_con_falla_queda_en_revision_y_registra_falla(
    db_session: Session,
):
    app.dependency_overrides[get_db] = lambda: db_session
    equipo = _crear_equipo(db_session, "OSC-0701", estado="Disponible")

    response = client.patch(
        f"/api/equipos/{equipo.codigo}/estado",
        json={"hubo_falla": True, "descripcion": "Botón de encendido dañado"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["estado"] == "En revisión"
    assert data["falla_id"] is not None

    db_session.refresh(equipo)
    assert equipo.estado == "En revisión"

    falla = db_session.get(Falla, data["falla_id"])
    assert falla is not None
    assert falla.descripcion == "Botón de encendido dañado"
    assert falla.sesion_equipo_id is None
    assert falla.equipo_id == equipo.id

    app.dependency_overrides.clear()


def test_cambiar_estado_con_falla_sin_descripcion_falla_validacion(
    db_session: Session,
):
    app.dependency_overrides[get_db] = lambda: db_session
    equipo = _crear_equipo(db_session, "OSC-0702")

    response = client.patch(
        f"/api/equipos/{equipo.codigo}/estado",
        json={"hubo_falla": True},
    )

    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_cambiar_estado_equipo_inexistente_404(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    response = client.patch(
        "/api/equipos/NO-EXISTE/estado",
        json={"hubo_falla": False},
    )

    assert response.status_code == 404

    app.dependency_overrides.clear()


def test_historial_de_fallas_previas_se_conserva_tras_nuevo_cambio(
    db_session: Session,
):
    """Un nuevo cambio de estado no debe borrar fallas ya registradas
    para el mismo equipo."""
    app.dependency_overrides[get_db] = lambda: db_session
    equipo = _crear_equipo(db_session, "OSC-0703", estado="Disponible")

    client.patch(
        f"/api/equipos/{equipo.codigo}/estado",
        json={"hubo_falla": True, "descripcion": "Falla histórica 1"},
    )
    client.patch(
        f"/api/equipos/{equipo.codigo}/estado",
        json={"hubo_falla": False},
    )
    client.patch(
        f"/api/equipos/{equipo.codigo}/estado",
        json={"hubo_falla": True, "descripcion": "Falla histórica 2"},
    )

    fallas = (
        db_session.query(Falla).filter(Falla.equipo_id == equipo.id).all()
    )
    assert len(fallas) == 2
    descripciones = {f.descripcion for f in fallas}
    assert descripciones == {"Falla histórica 1", "Falla histórica 2"}

    app.dependency_overrides.clear()

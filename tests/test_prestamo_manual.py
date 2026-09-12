"""Pruebas para el préstamo manual en un solo paso usando matrícula +
código de equipo (POST /api/sesiones/prestamo-manual, US-12)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_db
from app.main import app
from app.models.labtrack import Equipo, Estudiante, TipoEquipo

client = TestClient(app)


def _crear_estudiante(db_session: Session, matricula: str = "S21044444") -> Estudiante:
    estudiante = Estudiante(nombre="Alexander López", matricula=matricula)
    db_session.add(estudiante)
    db_session.commit()
    return estudiante


def _crear_equipo(
    db_session: Session, codigo: str = "OSC-0800", estado: str = "Disponible"
) -> Equipo:
    tipo = TipoEquipo(nombre=f"Tipo-{codigo}")
    db_session.add(tipo)
    db_session.commit()

    equipo = Equipo(codigo=codigo, tipo_equipo_id=tipo.id, estado=estado)
    db_session.add(equipo)
    db_session.commit()
    return equipo


def test_prestamo_manual_por_matricula_y_codigo(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    estudiante = _crear_estudiante(db_session)
    equipo = _crear_equipo(db_session)

    response = client.post(
        "/api/sesiones/prestamo-manual",
        json={"matricula": estudiante.matricula, "codigo_equipo": equipo.codigo},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["matricula"] == estudiante.matricula
    assert data["codigo_equipo"] == equipo.codigo
    assert data["sesion_id"] is not None

    db_session.refresh(equipo)
    assert equipo.estado == "Prestado"

    app.dependency_overrides.clear()


def test_prestamo_manual_estudiante_inexistente_404(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    equipo = _crear_equipo(db_session, codigo="OSC-0801")

    response = client.post(
        "/api/sesiones/prestamo-manual",
        json={"matricula": "NO-EXISTE", "codigo_equipo": equipo.codigo},
    )

    assert response.status_code == 404

    app.dependency_overrides.clear()


def test_prestamo_manual_equipo_inexistente_404(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    estudiante = _crear_estudiante(db_session, matricula="S21055551")

    response = client.post(
        "/api/sesiones/prestamo-manual",
        json={"matricula": estudiante.matricula, "codigo_equipo": "NO-EXISTE"},
    )

    assert response.status_code == 404

    app.dependency_overrides.clear()


def test_prestamo_manual_equipo_no_disponible_409(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    estudiante = _crear_estudiante(db_session, matricula="S21066661")
    equipo = _crear_equipo(db_session, codigo="OSC-0802", estado="Prestado")

    response = client.post(
        "/api/sesiones/prestamo-manual",
        json={"matricula": estudiante.matricula, "codigo_equipo": equipo.codigo},
    )

    assert response.status_code == 409

    app.dependency_overrides.clear()


def test_abrir_sesion_manual_por_matricula(db_session: Session):
    """POST /api/sesiones también debe aceptar 'matricula' en vez de
    'estudiante_id'."""
    app.dependency_overrides[get_db] = lambda: db_session
    estudiante = _crear_estudiante(db_session, matricula="S21077771")

    response = client.post(
        "/api/sesiones", json={"matricula": estudiante.matricula}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["matricula"] == estudiante.matricula
    assert data["estudiante_id"] == estudiante.id

    app.dependency_overrides.clear()


def test_abrir_sesion_manual_matricula_inexistente_404(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    response = client.post("/api/sesiones", json={"matricula": "NO-EXISTE"})

    assert response.status_code == 404

    app.dependency_overrides.clear()


def test_iniciar_devolucion_manual_por_codigo_equipo(db_session: Session):
    """POST /api/devoluciones también debe aceptar 'codigo_equipo' en vez
    de 'equipo_id'."""
    app.dependency_overrides[get_db] = lambda: db_session
    estudiante = _crear_estudiante(db_session, matricula="S21088881")
    equipo = _crear_equipo(db_session, codigo="OSC-0803", estado="Prestado")

    sesion_resp = client.post(
        "/api/sesiones", json={"matricula": estudiante.matricula}
    )
    sesion_id = sesion_resp.json()["sesion_id"]

    from app.models.labtrack import SesionEquipo

    sesion_equipo = SesionEquipo(
        sesion_id=sesion_id, equipo_id=equipo.id, estado="Prestado"
    )
    db_session.add(sesion_equipo)
    db_session.commit()

    response = client.post(
        "/api/devoluciones", json={"codigo_equipo": equipo.codigo}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["codigo_equipo"] == equipo.codigo
    assert data["matricula"] == estudiante.matricula
    assert data["sesion_equipo_id"] == sesion_equipo.id

    app.dependency_overrides.clear()


def test_iniciar_devolucion_manual_codigo_equipo_inexistente_404(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session

    response = client.post(
        "/api/devoluciones", json={"codigo_equipo": "NO-EXISTE"}
    )

    assert response.status_code == 404

    app.dependency_overrides.clear()

"""Pruebas para la consulta del historial de equipos (US-10)."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_db
from app.main import app
from app.models.labtrack import (
    Equipo,
    Estudiante,
    Sesion,
    SesionEquipo,
    TipoEquipo,
)

app.dependency_overrides = {}  # type: ignore[attr-defined]

client = TestClient(app)

def test_obtener_historial_equipo_por_codigo_exitoso(db_session: Session) -> None:
    """Verifica que el historial del equipo se pueda consultar 
    exitosamente utilizando su código físico (QR).
    """
    app.dependency_overrides[get_db] = lambda: db_session

    # 1. Preparar datos base con un código físico específico
    tipo_eq = TipoEquipo(nombre="Osciloscopio")
    db_session.add(tipo_eq)
    db_session.commit()

    codigo_qr = "OSC-0307"
    equipo = Equipo(codigo=codigo_qr, tipo_equipo_id=tipo_eq.id, estado="Disponible")
    db_session.add(equipo)
    db_session.commit()

    estudiante = Estudiante(nombre="María López", matricula="S333444")
    db_session.add(estudiante)
    db_session.commit()

    sesion = Sesion(estudiante_id=estudiante.id, estado="Cerrada")
    db_session.add(sesion)
    db_session.commit()

    # 2. Generar el préstamo
    prestamo = SesionEquipo(
        sesion_id=sesion.id,
        equipo_id=equipo.id,
        estado="Devuelto",
        fecha_prestamo=datetime.now(UTC),
    )
    db_session.add(prestamo)
    db_session.commit()

    # 3. Ejecutar la petición HTTP usando el código QR
    response = client.get(f"/api/equipos/codigo/{codigo_qr}/historial")

    # 4. Validar la respuesta
    assert response.status_code == 200
    data = response.json()

    assert data["equipo_id"] == equipo.id
    assert data["codigo"] == codigo_qr
    assert len(data["historial_usos"]) == 1
    assert data["historial_usos"][0]["estudiante_nombre"] == "María López"

    app.dependency_overrides.clear()

def test_obtener_historial_equipo_no_encontrado(db_session: Session):
    """Verifica que retorne 404 si el equipo no existe en la base de datos."""
    app.dependency_overrides[get_db] = lambda: db_session

    response = client.get("/api/equipos/9999/historial")
    
    assert response.status_code == 404
    assert "no encontrado" in response.json()["detail"].lower()

    app.dependency_overrides.clear()
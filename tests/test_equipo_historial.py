"""Pruebas para la consulta del historial de equipos (US-10)."""

from datetime import UTC, datetime

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

app.dependency_overrides = {}  # type: ignore[attr-defined]

client = TestClient(app)

def test_obtener_historial_equipo_exitoso(db_session: Session):
    """Verifica que el historial del equipo 
    devuelva sus usos, estudiantes y fallas correctamente."""
    app.dependency_overrides[get_db] = lambda: db_session

    # 1. Preparar datos base
    tipo_eq = TipoEquipo(nombre="Multímetro")
    db_session.add(tipo_eq)
    db_session.commit()

    equipo = Equipo(codigo="MULT-001", tipo_equipo_id=tipo_eq.id, estado="En revisión")
    db_session.add(equipo)
    db_session.commit()

    estudiante = Estudiante(nombre="Carlos Pérez", matricula="S222333")
    db_session.add(estudiante)
    db_session.commit()

    sesion = Sesion(estudiante_id=estudiante.id, estado="Cerrada")
    db_session.add(sesion)
    db_session.commit()

    # 2. Generar el préstamo / uso del equipo
    prestamo = SesionEquipo(
        sesion_id=sesion.id,
        equipo_id=equipo.id,
        estado="Devuelto",
        fecha_prestamo=datetime.now(UTC)
    )
    db_session.add(prestamo)
    db_session.commit()

    # 3. Registrar una falla asociada a este préstamo
    falla = Falla(
        equipo_id=equipo.id,
        sesion_equipo_id=prestamo.id,
        descripcion="Fusibles quemados",
        estado="Pendiente"
    )
    db_session.add(falla)
    db_session.commit()

    # 4. Ejecutar la petición HTTP
    response = client.get(f"/api/equipos/{equipo.id}/historial")

    # 5. Validar la respuesta
    assert response.status_code == 200
    data = response.json()

    assert data["equipo_id"] == equipo.id
    assert data["codigo"] == "MULT-001"
    assert data["tipo"] == "Multímetro"
    assert data["estado_actual"] == "En revisión"
    
    assert len(data["historial_usos"]) == 1
    uso = data["historial_usos"][0]
    assert uso["estudiante_nombre"] == "Carlos Pérez"
    assert uso["matricula_estudiante"] == "S222333"
    
    assert len(uso["fallas"]) == 1
    assert uso["fallas"][0]["descripcion"] == "Fusibles quemados"

    app.dependency_overrides.clear()

def test_obtener_historial_equipo_no_encontrado(db_session: Session):
    """Verifica que retorne 404 si el equipo no existe en la base de datos."""
    app.dependency_overrides[get_db] = lambda: db_session

    response = client.get("/api/equipos/9999/historial")
    
    assert response.status_code == 404
    assert "no encontrado" in response.json()["detail"].lower()

    app.dependency_overrides.clear()
"""Pruebas para la consulta del historial de estudiantes (US-11)."""

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
    SesionEquipoAccesorio,
    TipoAccesorio,
    TipoEquipo,
)

client = TestClient(app)

def test_obtener_historial_estudiante_exitoso(db_session: Session):
    """Verifica que el historial traiga las sesiones, 
    equipos, accesorios y fallas correctamente."""
    app.dependency_overrides[get_db] = lambda: db_session

    # 1. Preparar datos base
    estudiante = Estudiante(nombre="Alexander", matricula="S111222")
    db_session.add(estudiante)
    db_session.commit()

    sesion = Sesion(estudiante_id=estudiante.id, estado="Cerrada")
    db_session.add(sesion)
    db_session.commit()

    tipo_eq = TipoEquipo(nombre="Osciloscopio")
    db_session.add(tipo_eq)
    db_session.commit()

    equipo = Equipo(codigo="OSC-001", tipo_equipo_id=tipo_eq.id, estado="Disponible")
    db_session.add(equipo)
    db_session.commit()

    # 2. Generar el préstamo
    prestamo = SesionEquipo(
        sesion_id=sesion.id,
        equipo_id=equipo.id,
        estado="Devuelto",
        fecha_prestamo=datetime.now(UTC)
    )
    db_session.add(prestamo)
    db_session.commit()

    # 3. Vincular un accesorio y una falla al préstamo
    tipo_acc = TipoAccesorio(
        nombre="Sondas",
        tipo_equipo_id=tipo_eq.id,
        cantidad_default=2
    )
    db_session.add(tipo_acc)
    db_session.commit()

    accesorio = SesionEquipoAccesorio(
        sesion_equipo_id=prestamo.id,
        tipo_accesorio_id=tipo_acc.id,
        cantidad_prestada=2,
        cantidad_devuelta=2
    )
    db_session.add(accesorio)

    falla = Falla(
        equipo_id=equipo.id,
        sesion_equipo_id=prestamo.id,
        descripcion="Pantalla parpadea",
        estado="Pendiente"
    )
    db_session.add(falla)
    db_session.commit()

    # 4. Ejecutar la petición HTTP
    response = client.get(f"/api/estudiantes/{estudiante.id}/historial")

    # 5. Validar la respuesta de la API
    assert response.status_code == 200
    data = response.json()

    # Validar campos de raíz
    assert data["estudiante_id"] == estudiante.id
    assert data["nombre"] == "Alexander"
    assert len(data["sesiones"]) == 1

    # Validar la sesión
    sesion_data = data["sesiones"][0]
    assert sesion_data["sesion_id"] == sesion.id
    assert len(sesion_data["equipos"]) == 1

    # Validar el equipo, sus accesorios y sus fallas
    equipo_data = sesion_data["equipos"][0]
    assert equipo_data["codigo"] == "OSC-001"
    assert equipo_data["tipo"] == "Osciloscopio"
    
    assert len(equipo_data["accesorios"]) == 1
    assert equipo_data["accesorios"][0]["nombre"] == "Sondas"
    assert equipo_data["accesorios"][0]["cantidad_prestada"] == 2

    assert len(equipo_data["fallas"]) == 1
    assert equipo_data["fallas"][0]["descripcion"] == "Pantalla parpadea"

    app.dependency_overrides.clear()

def test_obtener_historial_estudiante_no_encontrado(db_session: Session):
    """Verifica que retorne 404 si el estudiante no existe en la BD."""
    app.dependency_overrides[get_db] = lambda: db_session

    response = client.get("/api/estudiantes/999/historial")
    
    assert response.status_code == 404
    assert "no encontrado" in response.json()["detail"].lower()

    app.dependency_overrides.clear()
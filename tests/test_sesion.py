import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_db
from app.main import app
from app.models.labtrack import Equipo, Estudiante, Sesion, SesionEquipo


@pytest.fixture
def client(db_session: Session):
    """Sobrescribe la DB real con la DB de pruebas para este archivo."""
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_cerrar_sesion_con_equipos_exitoso(
        client: TestClient, db_session: Session) -> None:
    # 1. Preparar datos en la base de datos de prueba
    estudiante = Estudiante(nombre="Alberto", matricula="S12345")
    db_session.add(estudiante)
    db_session.commit()

    equipo = Equipo(codigo="OSC-0500", tipo_equipo_id=1, estado="Disponible")
    db_session.add(equipo)
    db_session.commit()

    sesion = Sesion(estudiante_id=estudiante.id, estado="Activa")
    db_session.add(sesion)
    db_session.commit()

    # Vincular el equipo a la sesión
    sesion_equipo = SesionEquipo(
        sesion_id=sesion.id, 
        equipo_id=equipo.id, 
        estado="Prestado"
    )
    db_session.add(sesion_equipo)
    db_session.commit()

    # 2. Ejecutar la acción (Fase Roja: este endpoint aún no existe)
    response = client.post(f"/api/sesiones/{sesion.id}/cerrar")

    # 3. Validar resultados esperados
    assert response.status_code == 200
    data = response.json()
    assert data["sesion_id"] == sesion.id
    assert data["estado"] == "Cerrada"
    assert data["equipos_prestados"] == 1
    assert "mensaje" in data

    # 4. Validar persistencia en base de datos
    db_session.refresh(sesion)
    assert sesion.estado == "Cerrada"


def test_cerrar_sesion_vacia_falla(client: TestClient, db_session: Session) -> None:
    # 1. Preparar una sesión sin equipos asignados
    estudiante = Estudiante(nombre="Alex", matricula="S98765")
    db_session.add(estudiante)
    db_session.commit()

    sesion = Sesion(estudiante_id=estudiante.id, estado="Activa")
    db_session.add(sesion)
    db_session.commit()

    # 2. Ejecutar la acción
    response = client.post(f"/api/sesiones/{sesion.id}/cerrar")

    # 3. Validar que la regla de negocio bloquea el cierre
    assert response.status_code == 400
    assert response.json()["detail"] == "La sesión está vacía"

def test_cerrar_sesion_inexistente(client: TestClient) -> None:
    # Ejecutar la acción con un ID que no existe en la BD
    response = client.post("/api/sesiones/9999/cerrar")

    # Validar que el sistema responde correctamente con un 404
    assert response.status_code == 404
    assert response.json()["detail"] == "Sesión no encontrada"
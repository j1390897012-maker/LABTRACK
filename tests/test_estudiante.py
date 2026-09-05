from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app

client = TestClient(app)

def test_registrar_estudiante_exitoso(db_session):
    # 1. Redirigir la API hacia la base de datos temporal de pruebas
    app.dependency_overrides[get_db] = lambda: db_session
    
    response = client.post(
        "/api/estudiantes",
        json={"nombre": "Alexander Torres Andrade", "matricula": "S23013956"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "Alexander Torres Andrade"
    assert data["matricula"] == "S23013956"
    assert data["uid_rfid"] is None
    
    # 2. Limpiar la redirección al terminar
    app.dependency_overrides.clear()

def test_registrar_estudiante_matricula_duplicada(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Insertar el primer registro
    client.post(
        "/api/estudiantes",
        json={"nombre": "Alberto", "matricula": "S22012345"}
    )
    
    # Intentar registrar la misma matrícula
    response = client.post(
        "/api/estudiantes",
        json={"nombre": "Alejandro", "matricula": "S22012345"}
    )
    
    assert response.status_code == 409
    assert response.json()["detail"] == "La matrícula ya está registrada en el sistema."
    
    app.dependency_overrides.clear()
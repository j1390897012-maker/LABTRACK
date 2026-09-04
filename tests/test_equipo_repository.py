import os

from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app
from app.repositories.equipo_repository import EquipoRepository

client = TestClient(app)

def test_flujo_equipo_repository(db_session):
    repo = EquipoRepository()
    
    # 1. Probar creación del Tipo de Equipo
    tipo = repo.create_tipo(db=db_session, nombre="Multímetro")
    assert tipo.id is not None
    assert tipo.nombre == "Multímetro"
    
    # 2. Probar creación del Equipo físico
    equipo = repo.create(db=db_session, codigo="MULT-001", tipo_equipo_id=tipo.id)
    assert equipo.codigo == "MULT-001"
    assert equipo.estado == "Disponible"
    
    # 3. Probar la búsqueda del Equipo por código
    equipo_db = repo.get_by_codigo(db=db_session, codigo="MULT-001")
    assert equipo_db is not None
    assert equipo_db.id == equipo.id
    
    # 4. Probar búsqueda de un código que no existe
    equipo_inexistente = repo.get_by_codigo(db=db_session, codigo="FALSO-999")
    assert equipo_inexistente is None


def test_registrar_equipo_genera_qr(db_session): 
    # 0. Interceptar get_db para inyectar la base de datos de pruebas
    def override_get_db():
        yield db_session
        
    app.dependency_overrides[get_db] = override_get_db

    codigo_prueba = "TEST-QR-01"
    ruta_esperada = f"static/qrs/{codigo_prueba}.png"

    if os.path.exists(ruta_esperada):
        os.remove(ruta_esperada)

    response = client.post(
        "/api/equipos", 
        json={"codigo": codigo_prueba, "tipo": "Multimetro"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["codigo"] == codigo_prueba
    assert data["qr_path"] == ruta_esperada
    assert os.path.exists(ruta_esperada) is True

    os.remove(ruta_esperada)
    
    # 5. Limpiar la intercepción al terminar el test
    app.dependency_overrides.clear()
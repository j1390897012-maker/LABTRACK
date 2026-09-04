import os

from fastapi.testclient import TestClient

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
    assert equipo.estado == "Disponible"  # Verificando valor por defecto
    
    # 3. Probar la búsqueda del Equipo por código
    equipo_db = repo.get_by_codigo(db=db_session, codigo="MULT-001")
    assert equipo_db is not None
    assert equipo_db.id == equipo.id
    
    # 4. Probar búsqueda de un código que no existe
    equipo_inexistente = repo.get_by_codigo(db=db_session, codigo="FALSO-999")
    assert equipo_inexistente is None

def test_registrar_equipo_genera_qr():
    codigo_prueba = "TEST-QR-01"
    ruta_esperada = f"static/qrs/{codigo_prueba}.png"

    # 1. Preparación: asegurar que el archivo no exista de una prueba anterior
    if os.path.exists(ruta_esperada):
        os.remove(ruta_esperada)

    # 2. Ejecución: simular la petición POST
    response = client.post(
        "/api/equipos", 
        json={"codigo": codigo_prueba, "tipo": "Multimetro"}
    )

    # 3. Validación de la API
    assert response.status_code == 201
    data = response.json()
    assert data["codigo"] == codigo_prueba
    assert data["qr_path"] == ruta_esperada

    # 4. Validación del sistema de archivos: el QR físico debe existir
    assert os.path.exists(ruta_esperada) is True

    # 5. Limpieza: borrar el archivo generado para no ensuciar el repositorio
    os.remove(ruta_esperada)
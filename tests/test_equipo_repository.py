from app.repositories.equipo_repository import EquipoRepository


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
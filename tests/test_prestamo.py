"""Pruebas para el registro de préstamos y accesorios (US-03 y US-04)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_db
from app.main import app
from app.models.labtrack import (
    Equipo,
    Estudiante,
    Sesion,
    SesionEquipo,
    SesionEquipoAccesorio,
    TipoAccesorio,
    TipoEquipo,
)

client = TestClient(app)

def test_registrar_prestamo_con_accesorios(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    
    # 1. Preparar datos base
    tipo = TipoEquipo(nombre="Multímetro")
    db_session.add(tipo)
    db_session.commit()
    
    acc = TipoAccesorio(nombre="Cables", tipo_equipo_id=tipo.id, cantidad_default=2)
    db_session.add(acc)
    
    equipo = Equipo(codigo="MULT-001", tipo_equipo_id=tipo.id, estado="Disponible")
    db_session.add(equipo)
    
    estudiante = Estudiante(nombre="Alexander", matricula="S111222")
    db_session.add(estudiante)
    db_session.commit()
    
    sesion = Sesion(estudiante_id=estudiante.id, estado="Activa")
    db_session.add(sesion)
    db_session.commit()

    # 2. Ejecutar petición de préstamo con accesorios (US-04)
    response = client.post(
        "/api/equipos/prestar",
        json={
            "sesion_id": sesion.id,
            "equipo_id": equipo.id,
            "accesorios": [
                {"tipo_accesorio_id": acc.id, "cantidad": 2}
            ]
        }
    )
    
    # 3. Validar respuesta HTTP
    assert response.status_code == 200
    assert "registrados correctamente" in response.json()["mensaje"]
    
    # 4. Validar impacto en base de datos
    db_session.refresh(equipo)
    assert equipo.estado == "Prestado"
    
    prestamo = db_session.query(SesionEquipo).filter_by(equipo_id=equipo.id).first()
    assert prestamo is not None
    assert prestamo.estado == "Prestado"
    
    accesorios_prestados = db_session.query(SesionEquipoAccesorio).filter_by(
        sesion_equipo_id=prestamo.id
    ).all()
    assert len(accesorios_prestados) == 1
    assert accesorios_prestados[0].cantidad_prestada == 2
    
    app.dependency_overrides.clear()

def test_registrar_prestamo_equipo_no_disponible(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Preparar equipo que ya está prestado
    tipo = TipoEquipo(nombre="Cautín")
    db_session.add(tipo)
    db_session.commit()
    
    equipo = Equipo(codigo="CAU-001", tipo_equipo_id=tipo.id, estado="Prestado")
    db_session.add(equipo)
    db_session.commit()
    
    response = client.post(
        "/api/equipos/prestar",
        json={
            "sesion_id": 1, # ID simulado, no llegará a validarse
            "equipo_id": equipo.id,
            "accesorios": []
        }
    )
    
    assert response.status_code == 409
    assert "no está disponible" in response.json()["detail"]
    
    app.dependency_overrides.clear()

def test_registrar_prestamo_cantidad_accesorios_invalida(db_session):
    """Verifica que el sistema rechace cantidades nulas o negativas (US-04)."""
    # No necesitamos insertar datos en la BD real porque 
    # Pydantic debe bloquear la petición antes de llegar al servicio.
    
    response = client.post(
        "/api/equipos/prestar",
        json={
            "sesion_id": 1,
            "equipo_id": 1,
            "accesorios": [
                {"tipo_accesorio_id": 1, "cantidad": 0}  # Cantidad inválida
            ]
        }
    )
    
    assert response.status_code == 422
    errores = response.json()["detail"]
    assert any(error["loc"][-1] == "cantidad" for error in errores)
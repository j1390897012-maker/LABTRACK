# En esta Capa de Servicio (Service Layer) es donde ocurre la verdadera
# toma de decisiones del sistema. Al mantener esta lógica separada de 
# las rutas de internet, se está aplicando el principio de Responsabilidad
# Única (Single Responsibility Principle de SOLID), lo que demuestra un 
# diseño de software profesional.

# El contrato de la API dice claramente que si intentamos registrar a un
# estudiante con una matrícula repetida, el sistema debe arrojar un 
# error 409 Conflict.

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.labtrack import Estudiante
from app.schemas.estudiante import EstudianteCreate


def crear_estudiante(db: Session, estudiante_in: EstudianteCreate) -> Estudiante:
    # 1. Regla de negocio: Verificar si la matrícula ya existe

    estudiante_existente = (
        db.query(Estudiante)
        .filter(Estudiante.matricula == estudiante_in.matricula)
        .first()
    )
       
    if estudiante_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="La matrícula ya está registrada en el sistema."
        )
    
    # 2. Construir el nuevo registro
    nuevo_estudiante = Estudiante(
        nombre=estudiante_in.nombre,
        matricula=estudiante_in.matricula
    )
    
    # 3. Transacción en la base de datos
    db.add(nuevo_estudiante)
    db.commit()
    db.refresh(nuevo_estudiante)
    
    return nuevo_estudiante
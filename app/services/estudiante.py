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
from app.repositories.estudiante_repository import EstudianteRepository
from app.schemas.estudiante import EstudianteCreate

repo = EstudianteRepository()

def crear_estudiante(db: Session, estudiante_in: EstudianteCreate) -> Estudiante:
    estudiante_existente = repo.get_by_matricula(db=db,
    matricula=estudiante_in.matricula)
    
    if estudiante_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="La matrícula ya está registrada en el sistema."
        )
    
    nuevo_estudiante = repo.create(db=db, estudiante_in=estudiante_in)
    return nuevo_estudiante
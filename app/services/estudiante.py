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
    
    # El servicio extrae los datos del schema y los pasa al repository
    nuevo_estudiante = repo.create(
        db=db, 
        nombre=estudiante_in.nombre, 
        matricula=estudiante_in.matricula
    )
    return nuevo_estudiante
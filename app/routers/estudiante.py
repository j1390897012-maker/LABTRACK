from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

# Asegúrate de que la importación de get_db coincida con tu proyecto
from app.db import get_db
from app.schemas.estudiante import EstudianteCreate, EstudianteResponse
from app.services.estudiante import crear_estudiante

router = APIRouter(
    prefix="/api/estudiantes",
    tags=["Estudiantes"]
)

@router.post("", response_model=EstudianteResponse, status_code=status.HTTP_201_CREATED)
def registrar_estudiante(
    estudiante_in: EstudianteCreate, 
    db: Session = Depends(get_db)
) -> Any:
    """
    Registra un estudiante con nombre y matrícula en el sistema.
    """
    nuevo_estudiante = crear_estudiante(db=db, estudiante_in=estudiante_in)
    return nuevo_estudiante
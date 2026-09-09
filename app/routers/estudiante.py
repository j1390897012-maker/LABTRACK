from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

# Asegúrate de que la importación de get_db coincida con tu proyecto
from app.db import get_db
from app.schemas.estudiante import EstudianteCreate, EstudianteResponse
from app.schemas.historial import HistorialEstudianteResponse
from app.services.estudiante import crear_estudiante
from app.services.estudiante_service import EstudianteService

router = APIRouter(
    prefix="/api/estudiantes",
    tags=["Estudiantes"]
)

estudiante_service = EstudianteService()

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

@router.get(
    "/{estudiante_id}/historial", 
    response_model=HistorialEstudianteResponse,
    status_code=status.HTTP_200_OK
)
def obtener_historial_estudiante(
    estudiante_id: int,
    db: Session = Depends(get_db)
) -> HistorialEstudianteResponse:
    """Consulta el historial completo de préstamos y 
    sesiones de un estudiante (US-11)."""
    return estudiante_service.obtener_historial(db, estudiante_id)
"""
Router de Equipos (app/routers/equipo.py)

Expone los endpoints HTTP de la API REST para la gestión de equipos de laboratorio.
Actúa como la "Puerta" de la arquitectura: recibe las peticiones, inyecta 
la conexión a la base de datos y delega toda la lógica al EquipoService.

Implementa:
- US-01: POST /api/equipos -> Registra un equipo nuevo en el sistema.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.equipo import EquipoCreate, EquipoOut
from app.services.equipo_service import EquipoService

router = APIRouter(prefix="/api/equipos", tags=["Equipos"])
equipo_service = EquipoService()

@router.post("", response_model=EquipoOut, status_code=status.HTTP_201_CREATED)
def registrar_equipo(
    equipo_in: EquipoCreate, 
    db: Annotated[Session, Depends(get_db)]
):
    return equipo_service.registrar_equipo(db, equipo_in)
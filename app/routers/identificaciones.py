from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.identificacion import (
    AsignacionRFIDRequest,
    AsignacionRFIDResponse,
    IdentificacionResponse,
)
from app.services.identificaciones import IdentificacionService

router = APIRouter(
    prefix="/api/identificaciones",
    tags=["Identificación"],
)

identificacion_service = IdentificacionService()


@router.post(
    "/scan",
    response_model=IdentificacionResponse,
    status_code=status.HTTP_200_OK,
)
def escanear_rfid(
    uid_rfid: str,
    db: Session = Depends(get_db),
) -> IdentificacionResponse:
    """Escanea una credencial RFID y devuelve el estudiante asociado (si existe)."""
    return identificacion_service.escanear_rfid(db, uid_rfid)


@router.post(
    "/enrolar",
    response_model=AsignacionRFIDResponse,
    status_code=status.HTTP_200_OK,
)
def enrolar_rfid(
    asignacion_data: AsignacionRFIDRequest,
    db: Session = Depends(get_db),
) -> AsignacionRFIDResponse:
    """Enrolar un RFID a un estudiante existente."""
    return identificacion_service.enrolar_rfid(db, asignacion_data)
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

# Asegúrate de que la ruta coincida con tu proyecto
from app.db import get_db
from app.schemas.identificacion import (
    AsignacionRFIDRequest,
    AsignacionRFIDResponse,
    IdentificacionResponse,
    ScanRequest,
)
from app.services.identificaciones import IdentificacionService

router = APIRouter(
    prefix="/api/identificaciones",
    tags=["Identificaciones"]
)

identificacion_service = IdentificacionService()

@router.post(
    "/scan", 
    response_model=IdentificacionResponse, 
    status_code=status.HTTP_200_OK)
def escanear_identificacion(
    request: ScanRequest, 
    db: Session = Depends(get_db)
) -> Any:
    """
    Endpoint principal para el hardware (ESP32). 
    Recibe un escaneo (RFID o QR) y delega la decisión al servicio.
    """
    return identificacion_service.procesar_escaneo(db=db, request=request)

@router.post(
    "/enrolar", 
    response_model=AsignacionRFIDResponse, 
    status_code=status.HTTP_200_OK)
def enrolar_tarjeta_rfid(
    request: AsignacionRFIDRequest, 
    db: Session = Depends(get_db)
) -> Any:
    """
    Asocia un UID de tarjeta RFID a un estudiante existente (US-09).
    """
    return identificacion_service.enrolar_rfid(db=db, asignacion_data=request)
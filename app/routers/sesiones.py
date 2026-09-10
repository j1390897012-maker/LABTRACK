from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.sesion import (
    AbrirSesionManualRequest,
    AbrirSesionManualResponse,
    AgregarEquipoManualRequest,
    AgregarEquipoManualResponse,
    CierreSesionResponse,
)
from app.services.sesion_service import SesionService

router = APIRouter(prefix="/api/sesiones", tags=["Sesiones"])
sesion_service = SesionService()

@router.post("/{sesion_id}/cerrar", response_model=CierreSesionResponse)
def cerrar_sesion_prestamo(sesion_id: int, db: 
                           Session = Depends(get_db))-> CierreSesionResponse:
    """
    Cierra una sesión de préstamo.
    """
    return sesion_service.cerrar_entrega(db, sesion_id)


@router.post(
    "",
    response_model=AbrirSesionManualResponse,
    status_code=status.HTTP_201_CREATED,
)
def abrir_sesion_manual(
    request: AbrirSesionManualRequest,
    db: Session = Depends(get_db),
) -> AbrirSesionManualResponse:
    """Abre manualmente una sesión seleccionando al estudiante (US-12)."""
    return sesion_service.abrir_sesion_manual(db, request.estudiante_id)


@router.post(
    "/{sesion_id}/equipos",
    response_model=AgregarEquipoManualResponse,
    status_code=status.HTTP_200_OK,
)
def agregar_equipo_manual(
    sesion_id: int,
    request: AgregarEquipoManualRequest,
    db: Session = Depends(get_db),
) -> AgregarEquipoManualResponse:
    """Agrega manualmente un equipo a una sesión abierta (US-12)."""
    return sesion_service.agregar_equipo_manual(db, sesion_id, request)
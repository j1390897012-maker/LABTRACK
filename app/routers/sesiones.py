from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.sesion import (
    AbrirSesionManualRequest,
    AbrirSesionManualResponse,
    AgregarEquipoManualRequest,
    AgregarEquipoManualResponse,
    CierreSesionResponse,
    PrestamoManualRequest,
    PrestamoManualResponse,
    SesionActivaResponse,
)
from app.services.sesion_service import SesionService

router = APIRouter(prefix="/api/sesiones", tags=["Sesiones"])
sesion_service = SesionService()

@router.get(
    "/activa", response_model=SesionActivaResponse, status_code=status.HTTP_200_OK
)
def obtener_sesion_activa(
    matricula: str,
    db: Session = Depends(get_db),
) -> SesionActivaResponse:
    """Consulta la sesión activa de un estudiante por su matrícula, junto
    con los equipos actualmente prestados en ella."""
    return sesion_service.sesion_activa_por_matricula(db, matricula)


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
    """Abre manualmente una sesión seleccionando al estudiante por
    matrícula (US-12)."""
    return sesion_service.abrir_sesion_manual(db, request)


@router.post(
    "/prestamo-manual",
    response_model=PrestamoManualResponse,
    status_code=status.HTTP_201_CREATED,
)
def prestamo_manual(
    request: PrestamoManualRequest,
    db: Session = Depends(get_db),
) -> PrestamoManualResponse:
    """US-12: registra en un solo paso un préstamo manual usando la
    matrícula del estudiante y el código QR del equipo (abre/reutiliza la
    sesión internamente)."""
    return sesion_service.prestamo_manual(db, request)


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
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.sesion import CierreSesionResponse
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
"""
Router de Equipos (app/routers/equipo.py)

Expone los endpoints HTTP de la API REST para la gestión de equipos de laboratorio.
Actúa como la "Puerta" de la arquitectura: recibe las peticiones, inyecta 
la conexión a la base de datos y delega toda la lógica al EquipoService.

Implementa:
- US-01: POST /api/equipos -> Registra un equipo nuevo en el sistema.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.equipo import EquipoCreate, EquipoOut
from app.schemas.historial_equipo import HistorialEquipoResponse
from app.schemas.prestamo import ConfirmarPrestamoRequest
from app.services.equipo_service import EquipoService
from app.services.prestamo_service import PrestamoService

router = APIRouter(prefix="/api/equipos", tags=["Equipos"])
equipo_service = EquipoService()
prestamo_service = PrestamoService()

@router.post("", response_model=EquipoOut, status_code=status.HTTP_201_CREATED)
def registrar_equipo(
    equipo_in: EquipoCreate, 
    db: Annotated[Session, Depends(get_db)]
) -> dict[str, Any]:
    return equipo_service.registrar_equipo(db, equipo_in)

@router.post("/prestar", status_code=status.HTTP_200_OK)
def registrar_prestamo(
    request: ConfirmarPrestamoRequest, 
    db: Session = Depends(get_db)
) -> Any:
    """
    Confirma el préstamo de un equipo y registra los accesorios entregados.
    """
    return prestamo_service.confirmar_prestamo(db=db, request=request)

@router.get(
    "/{equipo_id}/historial",
    response_model=HistorialEquipoResponse,
    status_code=status.HTTP_200_OK
)
def obtener_historial_equipo(
    equipo_id: int,
    db: Session = Depends(get_db)
) -> HistorialEquipoResponse:
    """Consulta el historial completo de 
    un equipo, incluyendo quién lo usó y sus fallas (US-10)."""
    return equipo_service.obtener_historial(db, equipo_id)

@router.get(
    "/codigo/{codigo}/historial",
    response_model=HistorialEquipoResponse,
    status_code=status.HTTP_200_OK,
)
def obtener_historial_equipo_por_codigo(
    codigo: str, db: Session = Depends(get_db)
) -> HistorialEquipoResponse:
    """Consulta el historial completo de un equipo escaneando su código QR,
    obteniendo su ID interno y consultando su trazabilidad (US-10).
    """
    return equipo_service.obtener_historial_por_codigo(db, codigo)
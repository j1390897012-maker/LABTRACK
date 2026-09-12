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
from app.schemas.equipo import (
    CambioEstadoEquipoRequest,
    CambioEstadoEquipoResponse,
    EquipoCreate,
    EquipoDetalleResponse,
    EquipoListItem,
    EquipoOut,
)
from app.schemas.historial import HistorialEquipoResponse
from app.schemas.prestamo import ConfirmarPrestamoRequest, ConfirmarPrestamoResponse
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

@router.get("", response_model=list[EquipoListItem], status_code=status.HTTP_200_OK)
def listar_equipos(
    codigo: str | None = None,
    estado: str | None = None,
    tipo: str | None = None,
    db: Session = Depends(get_db),
) -> list[EquipoListItem]:
    """Lista/busca equipos por código (parcial), estado y/o tipo."""
    return equipo_service.listar(db, codigo=codigo, estado=estado, tipo=tipo)

@router.post(
    "/prestar",
    response_model=ConfirmarPrestamoResponse,
    status_code=status.HTTP_200_OK,
)
def registrar_prestamo(
    request: ConfirmarPrestamoRequest, 
    db: Session = Depends(get_db)
) -> ConfirmarPrestamoResponse:
    """
    Confirma el préstamo de un equipo y registra los accesorios entregados.
    """
    return prestamo_service.confirmar_prestamo(db=db, request=request)

@router.get(
    "/{codigo}",
    response_model=EquipoDetalleResponse,
    status_code=status.HTTP_200_OK,
)
def obtener_detalle_equipo(
    codigo: str,
    db: Session = Depends(get_db),
) -> EquipoDetalleResponse:
    """Detalle de un equipo identificado por su código QR (p. ej. OSC-0307)."""
    return equipo_service.obtener_detalle(db, codigo)

@router.get(
    "/{codigo}/historial",
    response_model=HistorialEquipoResponse,
    status_code=status.HTTP_200_OK,
)
def obtener_historial_equipo(
    codigo: str,
    db: Session = Depends(get_db),
) -> HistorialEquipoResponse:
    """Historial completo de préstamos de un equipo, identificado por su
    código QR, más reciente primero (US-10)."""
    return equipo_service.obtener_historial(db, codigo)

@router.patch(
    "/{codigo}/estado",
    response_model=CambioEstadoEquipoResponse,
    status_code=status.HTTP_200_OK,
)
def cambiar_estado_equipo(
    codigo: str,
    request: CambioEstadoEquipoRequest,
    db: Session = Depends(get_db),
) -> CambioEstadoEquipoResponse:
    """Cambia manualmente el estado de un equipo (identificado por su
    código QR) desde la pantalla de detalle. Si hubo falla, el equipo
    queda 'En revisión' y se registra la falla; si no, queda
    'Disponible'."""
    return equipo_service.cambiar_estado(db, codigo, request)
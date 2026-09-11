from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.falla import FallaDetalleResponse, FallaListItem
from app.services.falla_service import FallaService

router = APIRouter(prefix="/api/fallas", tags=["Fallas"])
falla_service = FallaService()


@router.get("", response_model=list[FallaListItem], status_code=status.HTTP_200_OK)
def listar_fallas(
    estado: str | None = None,
    db: Session = Depends(get_db),
) -> list[FallaListItem]:
    """Lista fallas, opcionalmente filtradas por estado (p. ej.
    ?estado=Pendiente). El equipo se identifica por su código QR."""
    return falla_service.listar(db, estado=estado)


@router.get(
    "/{falla_id}",
    response_model=FallaDetalleResponse,
    status_code=status.HTTP_200_OK,
)
def obtener_detalle_falla(
    falla_id: int,
    db: Session = Depends(get_db),
) -> FallaDetalleResponse:
    """Detalle de una falla específica."""
    return falla_service.obtener_detalle(db, falla_id)

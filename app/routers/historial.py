"""Router de Historial Global (app/routers/historial.py).

Complementa a GET /api/equipos/{codigo}/historial y
GET /api/estudiantes/{estudiante_id}/historial: este endpoint no
requiere un id/código previo, para poblar la pestaña "Historial"
directamente con la actividad reciente de todo el laboratorio.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.historial import HistorialGlobalResponse
from app.services.historial_service import HistorialService

router = APIRouter(prefix="/api/historial", tags=["Historial"])
historial_service = HistorialService()


@router.get(
    "",
    response_model=HistorialGlobalResponse,
    status_code=status.HTTP_200_OK,
)
def obtener_historial_global(
    desde: datetime | None = None,
    hasta: datetime | None = None,
    tipo: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> HistorialGlobalResponse:
    """Actividad reciente de todo el laboratorio (préstamos,
    devoluciones, fallas y resoluciones de falla), más reciente primero.

    `tipo` filtra por uno de: 'prestamo', 'devolucion', 'falla',
    'resolucion_falla'. `desde`/`hasta` filtran por fecha (ISO 8601).
    """
    return historial_service.obtener_global(
        db, desde=desde, hasta=hasta, tipo=tipo, limit=limit, offset=offset
    )

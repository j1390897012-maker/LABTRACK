from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.catalogo import TipoAccesorioOut, TipoEquipoOut
from app.services.catalogo_service import CatalogoService

router = APIRouter(prefix="/api", tags=["Catálogos"])
catalogo_service = CatalogoService()


@router.get(
    "/tipos-equipo",
    response_model=list[TipoEquipoOut],
    status_code=status.HTTP_200_OK,
)
def listar_tipos_equipo(db: Session = Depends(get_db)) -> list[TipoEquipoOut]:
    """Catálogo de tipos de equipo (para registrar/filtrar equipos)."""
    return catalogo_service.listar_tipos_equipo(db)


@router.get(
    "/tipos-accesorio",
    response_model=list[TipoAccesorioOut],
    status_code=status.HTTP_200_OK,
)
def listar_tipos_accesorio(
    tipo_equipo_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[TipoAccesorioOut]:
    """Catálogo de tipos de accesorio, opcionalmente filtrado por tipo de
    equipo (para seleccionar accesorios en préstamo/devolución)."""
    return catalogo_service.listar_tipos_accesorio(db, tipo_equipo_id=tipo_equipo_id)

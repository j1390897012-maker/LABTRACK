from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.devolucion import ConfirmarDevolucionRequest
from app.services.devolucion import DevolucionService

router = APIRouter(
    prefix="/api/devoluciones",
    tags=["Devoluciones"],
)

devolucion_service = DevolucionService()


@router.post(
    "/accesorios",
    status_code=status.HTTP_200_OK,
)
def confirmar_devolucion_accesorios(
    request: ConfirmarDevolucionRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Confirma la devolución de accesorios de un préstamo."""
    return devolucion_service.confirmar_devolucion(
        db=db,
        request=request,
    )
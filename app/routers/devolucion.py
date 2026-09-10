from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.devolucion import (
    ConfirmarDevolucionRequest,
    IniciarDevolucionManualRequest,
    IniciarDevolucionManualResponse,
    RegistrarFallaRequest,
    RegistrarFallaResponse,
)
from app.services.devolucion import DevolucionService

router = APIRouter(
    prefix="/api/devoluciones",
    tags=["Devoluciones"],
)

devolucion_service = DevolucionService()


@router.post(
    "",
    response_model=IniciarDevolucionManualResponse,
    status_code=status.HTTP_200_OK,
)
def iniciar_devolucion_manual(
    request: IniciarDevolucionManualRequest,
    db: Session = Depends(get_db),
) -> IniciarDevolucionManualResponse:
    """Inicia manualmente una devolución seleccionando el equipo (US-12)."""
    return devolucion_service.iniciar_devolucion_manual(db=db, request=request)


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


@router.patch(
    "/{sesion_equipo_id}/falla",
    response_model=RegistrarFallaResponse,
    status_code=status.HTTP_200_OK,
)
def registrar_falla_devolucion(
    sesion_equipo_id: int,
    request: RegistrarFallaRequest,
    db: Session = Depends(get_db),
) -> RegistrarFallaResponse:
    """Registra si hubo o no una falla al devolver un equipo (US-08)."""
    return devolucion_service.registrar_falla(
        db=db,
        sesion_equipo_id=sesion_equipo_id,
        request=request,
    )
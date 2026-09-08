""" Crear servicio de devolucion de equipos"""


from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.sesion_repository import SesionRepository
from app.schemas.devolucion import ConfirmarDevolucionRequest


class DevolucionService:
    
    def __init__(self)-> None:
        self.repo_sesion = SesionRepository()

    def confirmar_devolucion(
        self,
        db: Session,
        request: ConfirmarDevolucionRequest,
    ) -> dict[str, str]:
        """Registra la cantidad de accesorios devueltos de un préstamo."""

        # 1. Verificar que el préstamo exista
        prestamo = self.repo_sesion.get_sesion_equipo_by_id(
            db,
            request.sesion_equipo_id,
        )

        if not prestamo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Préstamo de equipo no encontrado.",
            )

        # 2. Procesar cada accesorio devuelto
        for accesorio_data in request.accesorios:
            accesorio = self.repo_sesion.get_accesorio_prestamo(
                db,
                request.sesion_equipo_id,
                accesorio_data.tipo_accesorio_id,
            )

            if not accesorio:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        "El accesorio no pertenece al préstamo "
                        "indicado."
                    ),
                )

            # 3. No permitir devolver más unidades de las prestadas
            if accesorio_data.cantidad_devuelta > accesorio.cantidad_prestada:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "La cantidad devuelta no puede ser mayor "
                        "a la cantidad prestada."
                    ),
                )

            # 4. Guardar la cantidad devuelta
            self.repo_sesion.actualizar_cantidad_devuelta(
                db,
                accesorio,
                accesorio_data.cantidad_devuelta,
            )

        return {
            "mensaje": "Devolución de accesorios registrada correctamente."
        }
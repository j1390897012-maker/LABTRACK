from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.labtrack import Sesion
from app.repositories.sesion_repository import SesionRepository
from app.schemas.sesion import CierreSesionResponse


class SesionService:
    def __init__(self) -> None:
        self.repo_sesion = SesionRepository()

    def cerrar_entrega(self, db: Session, sesion_id: int) -> CierreSesionResponse:
        sesion = db.get(Sesion, sesion_id)
        if not sesion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Sesión no encontrada"
            )

        equipos = self.repo_sesion.get_equipos_by_sesion(db, sesion_id)
        
        # Regla de negocio US-05: No cerrar sesiones vacías
        if not equipos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="La sesión está vacía"
            )

        self.repo_sesion.cerrar_sesion(db, sesion)

        return CierreSesionResponse(
            sesion_id=sesion.id,
            estado=sesion.estado,
            mensaje="Entrega cerrada exitosamente. Equipos marcados como prestados.",
            equipos_prestados=len(equipos)
        )
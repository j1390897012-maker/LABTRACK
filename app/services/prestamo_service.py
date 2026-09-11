from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.equipo_repository import EquipoRepository
from app.repositories.sesion_repository import SesionRepository
from app.schemas.prestamo import ConfirmarPrestamoRequest, ConfirmarPrestamoResponse


class PrestamoService:
    def __init__(self) -> None:
        self.repo_equipo = EquipoRepository()
        self.repo_sesion = SesionRepository()

    def confirmar_prestamo(
        self, db: Session, request: ConfirmarPrestamoRequest
    ) -> ConfirmarPrestamoResponse:
        # 1. Validar disponibilidad del equipo
        equipo = self.repo_equipo.get_by_id(db, request.equipo_id)
        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Equipo no encontrado"
            )
        if equipo.estado != "Disponible":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail=f"El equipo no está disponible (Estado actual: {equipo.estado})"
            )

        # 2. Generar el préstamo del equipo base (US-03)
        prestamo = self.repo_sesion.add_equipo(db, request.sesion_id, equipo)

        # 3. Registrar accesorios asociados (US-04)
        if request.accesorios:
            accesorios_dict = [
                {"tipo_accesorio_id": a.tipo_accesorio_id, "cantidad": a.cantidad}
                for a in request.accesorios
            ]
            self.repo_sesion.add_accesorios_prestamo(db, prestamo.id, accesorios_dict)

        return ConfirmarPrestamoResponse(
            sesion_id=request.sesion_id,
            equipo_id=equipo.id,
            codigo_equipo=equipo.codigo,
            mensaje="Préstamo y accesorios registrados correctamente",
        )
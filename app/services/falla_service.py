from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.labtrack import Falla
from app.repositories.falla_repository import FallaRepository
from app.schemas.falla import FallaDetalleResponse, FallaListItem


class FallaService:
    def __init__(self) -> None:
        self.repo_falla = FallaRepository()

    def _matricula_y_nombre(self, falla: Falla) -> tuple[str | None, str | None]:
        """Obtiene matrícula/nombre del estudiante asociado a la falla, si
        la falla proviene de una devolución (sesion_equipo_id no nulo)."""
        if falla.sesion_equipo and falla.sesion_equipo.sesion:
            estudiante = falla.sesion_equipo.sesion.estudiante
            return estudiante.matricula, estudiante.nombre
        return None, None

    def listar(self, db: Session, estado: str | None = None) -> list[FallaListItem]:
        """Lista fallas, opcionalmente filtradas por estado
        (GET /api/fallas?estado=Pendiente)."""
        fallas = self.repo_falla.list_all(db, estado=estado)
        items = []
        for f in fallas:
            matricula, estudiante_nombre = self._matricula_y_nombre(f)
            items.append(
                FallaListItem(
                    id=f.id,
                    codigo_equipo=f.equipo.codigo,
                    tipo_equipo=f.equipo.tipo_equipo.nombre,
                    descripcion=f.descripcion,
                    fecha=f.fecha,
                    estado=f.estado,
                    matricula=matricula,
                    estudiante_nombre=estudiante_nombre,
                    fecha_resolucion=f.fecha_resolucion,
                    observacion_resolucion=f.observacion_resolucion,
                )
            )
        return items

    def obtener_detalle(self, db: Session, falla_id: int) -> FallaDetalleResponse:
        """Detalle de una falla (GET /api/fallas/{id})."""
        falla = self.repo_falla.get_by_id(db, falla_id)
        if not falla:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Falla con id {falla_id} no encontrada.",
            )

        matricula, estudiante_nombre = self._matricula_y_nombre(falla)
        return FallaDetalleResponse(
            id=falla.id,
            codigo_equipo=falla.equipo.codigo,
            tipo_equipo=falla.equipo.tipo_equipo.nombre,
            descripcion=falla.descripcion,
            fecha=falla.fecha,
            estado=falla.estado,
            matricula=matricula,
            estudiante_nombre=estudiante_nombre,
            fecha_resolucion=falla.fecha_resolucion,
            observacion_resolucion=falla.observacion_resolucion,
        )

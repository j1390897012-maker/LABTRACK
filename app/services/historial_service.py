"""Service de Historial Global (app/services/historial_service.py)."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.repositories.historial_repository import HistorialRepository
from app.schemas.historial import HistorialGlobalItem, HistorialGlobalResponse


class HistorialService:
    def __init__(self) -> None:
        self.repo = HistorialRepository()

    def obtener_global(
        self,
        db: Session,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        tipo: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> HistorialGlobalResponse:
        """Feed cronológico (más reciente primero) de toda la actividad
        del laboratorio: préstamos, devoluciones, fallas registradas y
        fallas resueltas. Pensado para poblar la pestaña 'Historial'
        directamente, sin requerir filtrar antes por equipo o
        estudiante (GET /api/historial).

        `tipo` filtra por uno de: 'prestamo', 'devolucion', 'falla',
        'resolucion_falla'.
        """
        eventos: list[HistorialGlobalItem] = []

        for sesion_equipo in self.repo.list_sesion_equipos(db):
            estudiante = (
                sesion_equipo.sesion.estudiante if sesion_equipo.sesion else None
            )
            matricula = estudiante.matricula if estudiante else None
            estudiante_nombre = estudiante.nombre if estudiante else None
            codigo_equipo = sesion_equipo.equipo.codigo
            tipo_equipo = sesion_equipo.equipo.tipo_equipo.nombre

            eventos.append(
                HistorialGlobalItem(
                    tipo_evento="prestamo",
                    fecha=sesion_equipo.fecha_prestamo,
                    codigo_equipo=codigo_equipo,
                    tipo_equipo=tipo_equipo,
                    matricula=matricula,
                    estudiante_nombre=estudiante_nombre,
                    detalle=f"Préstamo de {codigo_equipo}",
                )
            )
            if sesion_equipo.fecha_devolucion is not None:
                eventos.append(
                    HistorialGlobalItem(
                        tipo_evento="devolucion",
                        fecha=sesion_equipo.fecha_devolucion,
                        codigo_equipo=codigo_equipo,
                        tipo_equipo=tipo_equipo,
                        matricula=matricula,
                        estudiante_nombre=estudiante_nombre,
                        detalle=f"Devolución de {codigo_equipo}",
                    )
                )

        for falla in self.repo.list_fallas(db):
            codigo_equipo = falla.equipo.codigo
            tipo_equipo = falla.equipo.tipo_equipo.nombre

            eventos.append(
                HistorialGlobalItem(
                    tipo_evento="falla",
                    fecha=falla.fecha,
                    codigo_equipo=codigo_equipo,
                    tipo_equipo=tipo_equipo,
                    detalle=falla.descripcion,
                )
            )
            if falla.fecha_resolucion is not None:
                eventos.append(
                    HistorialGlobalItem(
                        tipo_evento="resolucion_falla",
                        fecha=falla.fecha_resolucion,
                        codigo_equipo=codigo_equipo,
                        tipo_equipo=tipo_equipo,
                        detalle=falla.observacion_resolucion or "Falla resuelta",
                    )
                )

        if tipo:
            eventos = [e for e in eventos if e.tipo_evento == tipo]
        if desde:
            eventos = [e for e in eventos if e.fecha >= desde]
        if hasta:
            eventos = [e for e in eventos if e.fecha <= hasta]

        eventos.sort(key=lambda e: e.fecha, reverse=True)
        total = len(eventos)
        pagina = eventos[offset : offset + limit]

        return HistorialGlobalResponse(
            items=pagina,
            total=total,
            limit=limit,
            offset=offset,
        )

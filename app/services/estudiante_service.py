from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.estudiante_repository import EstudianteRepository
from app.schemas.historial import (
    HistorialAccesorio,
    HistorialEquipo,
    HistorialEstudianteResponse,
    HistorialFalla,
    HistorialSesion,
)


class EstudianteService:
    def __init__(self) -> None:
        self.repo_estudiante = EstudianteRepository()

    def obtener_historial(
        self, db: Session, estudiante_id: int
    ) -> HistorialEstudianteResponse:
        
        estudiante = self.repo_estudiante.get_historial_completo(db, estudiante_id)
        
        if not estudiante:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Estudiante no encontrado."
            )

        # Mapeo manual estructurado usando los modelos de Pydantic
        sesiones_historial = []
        for sesion in sorted(
        estudiante.sesiones,
        key=lambda s: s.fecha_apertura,
        reverse=True):
            equipos_historial = []
            
            for prestamo in sesion.sesion_equipos:
                accesorios = [
                    HistorialAccesorio(
                        nombre=acc.tipo_accesorio.nombre,
                        cantidad_prestada=acc.cantidad_prestada,
                        cantidad_devuelta=acc.cantidad_devuelta
                    ) for acc in prestamo.accesorios
                ]
                
                fallas = [
                    HistorialFalla(
                        id=f.id,
                        descripcion=f.descripcion,
                        estado=f.estado,
                        fecha=f.fecha
                    ) for f in prestamo.fallas
                ]

                equipos_historial.append(
                    HistorialEquipo(
                        codigo=prestamo.equipo.codigo,
                        tipo=prestamo.equipo.tipo_equipo.nombre,
                        estado_prestamo=prestamo.estado,
                        fecha_prestamo=prestamo.fecha_prestamo,
                        fecha_devolucion=prestamo.fecha_devolucion,
                        accesorios=accesorios,
                        fallas=fallas
                    )
                )

            sesiones_historial.append(
                HistorialSesion(
                    sesion_id=sesion.id,
                    estado=sesion.estado,
                    fecha_apertura=sesion.fecha_apertura,
                    fecha_cierre=sesion.fecha_cierre,
                    equipos=equipos_historial
                )
            )

        return HistorialEstudianteResponse(
            estudiante_id=estudiante.id,
            nombre=estudiante.nombre,
            matricula=estudiante.matricula,
            sesiones=sesiones_historial
        )
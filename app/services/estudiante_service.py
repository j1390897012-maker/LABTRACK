from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.estudiante_repository import EstudianteRepository
from app.schemas.estudiante import (
    EstudianteResponse,
    EstudianteUpdate,
)
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

    def buscar(
        self,
        db: Session,
        matricula: str | None = None,
        nombre: str | None = None,
    ) -> list[EstudianteResponse]:
        """Lista estudiantes, opcionalmente filtrando por matrícula y/o
        nombre (GET /api/estudiantes)."""
        estudiantes = self.repo_estudiante.search(
            db, matricula=matricula, nombre=nombre
        )
        return [EstudianteResponse.model_validate(e) for e in estudiantes]

    def actualizar(
        self,
        db: Session,
        estudiante_id: int,
        datos: EstudianteUpdate,
    ) -> EstudianteResponse:
        """Corrige un error de captura en nombre y/o matrícula
        (PUT /api/estudiantes/{id})."""
        estudiante = self.repo_estudiante.get_by_id(db, estudiante_id)
        if not estudiante:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Estudiante no encontrado.",
            )

        if datos.matricula and datos.matricula != estudiante.matricula:
            duplicado = self.repo_estudiante.get_by_matricula(
                db, datos.matricula
            )
            if duplicado:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe otro estudiante con esa matrícula.",
                )

        estudiante = self.repo_estudiante.update(
            db,
            estudiante,
            nombre=datos.nombre,
            matricula=datos.matricula,
        )
        return EstudianteResponse.model_validate(estudiante)

    def eliminar(self, db: Session, estudiante_id: int) -> None:
        """Elimina un estudiante (DELETE /api/estudiantes/{id}).

        Se rechaza con 409 si el estudiante ya tiene historial de
        préstamos, para no romper la trazabilidad del laboratorio
        (US-10/US-11). En ese caso, corregir datos con PUT en vez de
        borrar y recrear.
        """
        estudiante = self.repo_estudiante.get_by_id(db, estudiante_id)
        if not estudiante:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Estudiante no encontrado.",
            )

        if self.repo_estudiante.tiene_historial(db, estudiante_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "No se puede eliminar: el estudiante ya tiene "
                    "historial de préstamos. Usa PUT para corregir sus "
                    "datos en vez de eliminarlo."
                ),
            )

        self.repo_estudiante.delete(db, estudiante)

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
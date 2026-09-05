from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.estudiante_repository import EstudianteRepository
from app.schemas.identificacion import (
    AsignacionRFIDRequest,
    AsignacionRFIDResponse,
    IdentificacionResponse,
)


class IdentificacionService:
    def __init__(self) -> None:
        self.repo = EstudianteRepository()

    def escanear_rfid(self, db: Session, uid_rfid: str) -> IdentificacionResponse:
        """Procesa el escaneo de una credencial RFID."""
        estudiante = self.repo.get_by_rfid(db, uid_rfid)

        if estudiante:
            return IdentificacionResponse(
                estudiante_id=estudiante.id,
                nombre=estudiante.nombre,
                matricula=estudiante.matricula,
                uid_rfid=uid_rfid,
                estado="registrado",
                mensaje="Estudiante identificado correctamente",
            )

        # RFID no asignado: es un caso esperado, no lanzamos excepción
        # porque el encargado puede enrolarlo luego.
        return IdentificacionResponse(
            estudiante_id=None,
            nombre=None,
            matricula=None,
            uid_rfid=uid_rfid,
            estado="no_registrado",
            mensaje="RFID no asociado a ningún estudiante. "
                    "Puede ser enrolado manualmente desde el panel de control.",
        )

    def enrolar_rfid(self, 
    db: Session, 
    asignacion_data: AsignacionRFIDRequest) -> AsignacionRFIDResponse:
        """Asigna un RFID a un estudiante existente."""
        # 1. Verificar que el estudiante existe
        estudiante = self.repo.get_by_matricula(db, asignacion_data.matricula)
        if not estudiante:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Estudiante con matrícula {
                    asignacion_data.matricula} no encontrado",
            )

        # 2. Verificar que el RFID no esté ya asignado a otro estudiante
        estudiante_existente = self.repo.get_by_rfid(db, asignacion_data.valor)
        if (estudiante_existente and 
        estudiante_existente.id != asignacion_data.matricula):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"RFID {asignacion_data.valor} ya está asignado "
                       f"al estudiante '{estudiante_existente.nombre}'",
            )

        # 3. Asignar el RFID al estudiante
        estudiante_actualizado = self.repo.asignar_rfid(
            db,
            estudiante.id,
            asignacion_data.valor,
        )

        # 4. Respuesta de confirmación
        return AsignacionRFIDResponse(
            estudiante_id=estudiante_actualizado.id,
            nombre=estudiante_actualizado.nombre,
            matricula=estudiante_actualizado.matricula,
            uid_rfid=asignacion_data.valor,
            mensaje="RFID asignado exitosamente al estudiante",
        )
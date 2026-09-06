from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.estudiante_repository import EstudianteRepository
from app.repositories.sesion_repository import SesionRepository
from app.schemas.identificacion import (
    AsignacionRFIDRequest,
    AsignacionRFIDResponse,
    IdentificacionResponse,
    ScanRequest,
)


class IdentificacionService:
    def __init__(self) -> None:
        self.repo_estudiante = EstudianteRepository()
        self.repo_sesion = SesionRepository()

    def procesar_escaneo(
        self, db: Session, request: ScanRequest
        ) -> IdentificacionResponse:
        """Punto de entrada principal para el ESP32."""
        if request.tipo == "rfid":
            return self._procesar_rfid(db, request.valor)
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Tipo de escaneo no soportado actualmente."
        )

    def _procesar_rfid(self, db: Session, uid_rfid: str) -> IdentificacionResponse:
        """Procesa el escaneo de una credencial RFID de estudiante."""
        estudiante = self.repo_estudiante.get_by_rfid(db, uid_rfid)

        if not estudiante:
            return IdentificacionResponse(
                uid_rfid=uid_rfid,
                estado="no_registrado",
                mensaje=(
                    "RFID no asociado a ningún estudiante. "
                    "Puede ser enrolado manualmente."
                ),
            )

        # 1. Regla de negocio: Buscar si ya tiene una sesión abierta
        sesion = self.repo_sesion.get_activa_by_estudiante(db, estudiante.id)

        equipos: list[str] = []
        
        if sesion:
            accion = "sesion_continuada"
            # Omitimos la carga de equipos_actuales hasta que Alberto haga la US-03
        else:
            # 2. Regla de negocio: Abrir nueva sesión
            sesion = self.repo_sesion.create(db, estudiante.id)
            accion = "sesion_abierta"

        return IdentificacionResponse(
            estudiante_id=estudiante.id,
            nombre=estudiante.nombre,
            matricula=estudiante.matricula,
            uid_rfid=uid_rfid,
            estado="registrado",
            mensaje="Estudiante identificado correctamente",
            accion=accion,
            sesion_id=sesion.id,
            equipos_actuales=equipos
        )
    
    def enrolar_rfid(self, 
    db: Session, 
    asignacion_data: AsignacionRFIDRequest) -> AsignacionRFIDResponse:
        """Asigna un RFID a un estudiante existente."""
        # 1. Verificar que el estudiante existe
        estudiante = self.repo_estudiante.get_by_matricula(
        db, 
        asignacion_data.matricula
        )
        if not estudiante:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Estudiante con matrícula {
                    asignacion_data.matricula} no encontrado",
            )

        # 2. Verificar que el RFID no esté ya asignado a otro estudiante
        estudiante_existente = self.repo_estudiante.get_by_rfid(
        db, 
        asignacion_data.valor
        )
        if (estudiante_existente and 
        estudiante_existente.id != estudiante.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"RFID {asignacion_data.valor} ya está asignado "
                       f"al estudiante '{estudiante_existente.nombre}'",
            )

        # 3. Asignar el RFID al estudiante
        estudiante_actualizado = self.repo_estudiante.asignar_rfid(
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
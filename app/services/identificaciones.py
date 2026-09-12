from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.equipo_repository import EquipoRepository
from app.repositories.estudiante_repository import EstudianteRepository
from app.repositories.sesion_repository import SesionRepository
from app.schemas.identificacion import (
    AccesorioPrestamoInfo,
    AsignacionRFIDRequest,
    AsignacionRFIDResponse,
    EstudianteSesionInfo,
    IdentificacionResponse,
    PrestamoActivoInfo,
    QRScanResponse,
    QRUS06Response,
    ScanRequest,
)


class IdentificacionService:
    def __init__(self) -> None:
        self.repo_estudiante = EstudianteRepository()
        self.repo_sesion = SesionRepository()
        self.repo_equipo = EquipoRepository()  

    def procesar_escaneo(
        self, db: Session, request: ScanRequest
    ) -> IdentificacionResponse | QRScanResponse | QRUS06Response:
        """Punto de entrada principal para el ESP32."""

        if request.tipo == "rfid":
            return self._procesar_rfid(db, request.valor)

        if request.tipo == "qr":
            return self._procesar_qr(db, request.valor)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de escaneo no soportado actualmente.",
        )

    def _procesar_qr(
        self,
        db: Session,
        codigo_qr: str,
    ) -> QRUS06Response:
        """Procesa un QR de equipo según el flujo de US-06."""

        # 1. Buscar el equipo
        equipo = self.repo_equipo.get_by_codigo(db, codigo_qr)

        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Equipo con código '{codigo_qr}' no encontrado.",
            )

        # 2. Si está prestado, preparar la devolución
        if equipo.estado == "Prestado":
            prestamo = self.repo_sesion.get_prestamo_activo_by_equipo(
                db,
                equipo.id,
            )

            if not prestamo:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "El equipo figura como prestado, "
                        "pero no tiene un préstamo activo."
                    ),
                )

            estudiante = prestamo.sesion.estudiante

            accesorios = [
                AccesorioPrestamoInfo(
                    id=accesorio.tipo_accesorio.id,
                    nombre=accesorio.tipo_accesorio.nombre,
                    cantidad_prestada=accesorio.cantidad_prestada,
                )
                for accesorio in prestamo.accesorios
            ]

            estudiante_info = EstudianteSesionInfo(
                id=estudiante.id,
                nombre=estudiante.nombre,
                matricula=estudiante.matricula,
            )

            prestamo_info = PrestamoActivoInfo(
                estudiante=estudiante_info,
                accesorios=accesorios,
            )

            return QRUS06Response(
                equipo_id=equipo.id,
                codigo=equipo.codigo,
                estado=equipo.estado,
                mensaje="Préstamo activo encontrado. Iniciar devolución.",
                accion="iniciar_devolucion",
                prestamo=prestamo_info,
            )

        # 3. Si está disponible, buscar estudiantes con sesión activa
        if equipo.estado == "Disponible":
            sesiones_activas = self.repo_sesion.get_sesiones_activas(db)

            estudiantes = [
                EstudianteSesionInfo(
                    id=sesion.estudiante.id,
                    nombre=sesion.estudiante.nombre,
                    matricula=sesion.estudiante.matricula,
                )
                for sesion in sesiones_activas
            ]

            # 3.1 Ningún estudiante tiene sesión activa
            if not estudiantes:
                return QRUS06Response(
                    equipo_id=equipo.id,
                    codigo=equipo.codigo,
                    estado=equipo.estado,
                    mensaje="Equipo disponible. Modo consulta.",
                    accion="consulta",
                )

            # 3.2 Exactamente un estudiante
            if len(estudiantes) == 1:
                return QRUS06Response(
                    equipo_id=equipo.id,
                    codigo=equipo.codigo,
                    estado=equipo.estado,
                    mensaje=(
                        "Equipo disponible. "
                        "Confirmar préstamo al estudiante."
                    ),
                    accion="confirmar_prestamo",
                    estudiantes=estudiantes,
                )

            # 3.3 Varios estudiantes
            return QRUS06Response(
                equipo_id=equipo.id,
                codigo=equipo.codigo,
                estado=equipo.estado,
                mensaje="Equipo disponible. Seleccionar estudiante.",
                accion="seleccionar_estudiante",
                estudiantes=estudiantes,
            )

        # 4. Estado no contemplado actualmente
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Estado de equipo no soportado: {equipo.estado}",
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
            # US-03: se listan los códigos de los equipos que el
            # estudiante tiene actualmente prestados en esta sesión.
            equipos_prestados = self.repo_sesion.get_equipos_prestados_by_sesion(
                db, sesion.id
            )
            equipos = [se.equipo.codigo for se in equipos_prestados]
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
    
    def enrolar_rfid(
        self, 
        db: Session, 
        asignacion_data: AsignacionRFIDRequest
    ) -> AsignacionRFIDResponse:
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
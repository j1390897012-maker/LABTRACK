from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.labtrack import Estudiante, Sesion
from app.repositories.equipo_repository import EquipoRepository
from app.repositories.estudiante_repository import EstudianteRepository
from app.repositories.sesion_repository import SesionRepository
from app.schemas.prestamo import ConfirmarPrestamoRequest
from app.schemas.sesion import (
    AbrirSesionManualRequest,
    AbrirSesionManualResponse,
    AgregarEquipoManualRequest,
    AgregarEquipoManualResponse,
    CierreSesionResponse,
    EquipoActivoInfo,
    PrestamoManualRequest,
    PrestamoManualResponse,
    SesionActivaResponse,
)
from app.services.prestamo_service import PrestamoService


class SesionService:
    def __init__(self) -> None:
        self.repo_sesion = SesionRepository()
        self.repo_estudiante = EstudianteRepository()
        self.repo_equipo = EquipoRepository()
        self.prestamo_service = PrestamoService()

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

    def abrir_sesion_manual(
        self,
        db: Session,
        request: AbrirSesionManualRequest,
    ) -> AbrirSesionManualResponse:
        """US-12: abre (o reutiliza) una sesión seleccionando al estudiante
        manualmente desde la web, sin depender del lector RFID.

        La interfaz debe identificar al estudiante por `matricula`;
        `estudiante_id` se conserva solo por compatibilidad interna.

        Reutiliza la misma regla de negocio que el flujo automático
        (app.services.identificaciones): si el estudiante ya tiene una
        sesión activa, se reutiliza; si no, se crea una nueva.
        """
        estudiante = self._resolver_estudiante(
            db,
            estudiante_id=request.estudiante_id,
            matricula=request.matricula,
        )

        sesion = self.repo_sesion.get_activa_by_estudiante(db, estudiante.id)
        if sesion:
            mensaje = "El estudiante ya tiene una sesión activa; se reutiliza."
        else:
            sesion = self.repo_sesion.create(db, estudiante.id)
            mensaje = "Sesión manual abierta correctamente."

        return AbrirSesionManualResponse(
            sesion_id=sesion.id,
            estudiante_id=estudiante.id,
            matricula=estudiante.matricula,
            estado=sesion.estado,
            mensaje=mensaje,
        )

    def _resolver_estudiante(
        self,
        db: Session,
        estudiante_id: int | None,
        matricula: str | None,
    ) -> Estudiante:
        """Resuelve un estudiante priorizando `matricula` sobre
        `estudiante_id` (compatibilidad interna). Lanza 404 si no existe."""
        estudiante = None
        if matricula:
            estudiante = self.repo_estudiante.get_by_matricula(db, matricula)
        elif estudiante_id is not None:
            estudiante = self.repo_estudiante.get_by_id(db, estudiante_id)

        if not estudiante:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Estudiante no encontrado.",
            )
        return estudiante

    def sesion_activa_por_matricula(
        self, db: Session, matricula: str
    ) -> SesionActivaResponse:
        """Consulta la sesión activa de un estudiante por su matrícula,
        junto con los equipos actualmente prestados en ella."""
        estudiante = self.repo_estudiante.get_by_matricula(db, matricula)
        if not estudiante:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Estudiante no encontrado.",
            )

        sesion = self.repo_sesion.get_activa_by_estudiante(db, estudiante.id)
        if not sesion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El estudiante no tiene una sesión activa.",
            )

        equipos_prestados = self.repo_sesion.get_equipos_prestados_by_sesion(
            db, sesion.id
        )

        return SesionActivaResponse(
            sesion_id=sesion.id,
            estudiante_id=estudiante.id,
            matricula=estudiante.matricula,
            estado=sesion.estado,
            equipos=[
                EquipoActivoInfo(
                    codigo=se.equipo.codigo,
                    tipo=se.equipo.tipo_equipo.nombre,
                    fecha_prestamo=se.fecha_prestamo,
                )
                for se in equipos_prestados
            ],
        )

    def prestamo_manual(
        self, db: Session, request: PrestamoManualRequest
    ) -> PrestamoManualResponse:
        """US-12: registra en un solo paso un préstamo manual usando
        matrícula + código de equipo.

        Reutiliza `abrir_sesion_manual` (para obtener/crear la sesión) y
        `PrestamoService.confirmar_prestamo` (para registrar el préstamo),
        sin duplicar la lógica de negocio existente.
        """
        estudiante = self.repo_estudiante.get_by_matricula(db, request.matricula)
        if not estudiante:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Estudiante con matrícula '{request.matricula}' no encontrado.",
            )

        equipo = self.repo_equipo.get_by_codigo(db, request.codigo_equipo)
        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Equipo con código '{request.codigo_equipo}' no encontrado.",
            )

        sesion = self.repo_sesion.get_activa_by_estudiante(db, estudiante.id)
        if not sesion:
            sesion = self.repo_sesion.create(db, estudiante.id)

        self.prestamo_service.confirmar_prestamo(
            db,
            ConfirmarPrestamoRequest(
                sesion_id=sesion.id,
                equipo_id=equipo.id,
                accesorios=request.accesorios,
            ),
        )

        return PrestamoManualResponse(
            sesion_id=sesion.id,
            matricula=estudiante.matricula,
            codigo_equipo=equipo.codigo,
            mensaje="Préstamo manual registrado correctamente.",
        )

    def agregar_equipo_manual(
        self,
        db: Session,
        sesion_id: int,
        request: AgregarEquipoManualRequest,
    ) -> AgregarEquipoManualResponse:
        """US-12: agrega manualmente un equipo a una sesión.

        Delega en PrestamoService.confirmar_prestamo para procesar el
        préstamo con la MISMA lógica de negocio que el flujo normal
        (validación de disponibilidad, registro de accesorios, etc.).
        """
        if request.equipo_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Falta seleccionar un equipo para registrar el préstamo.",
            )

        sesion = db.get(Sesion, sesion_id)
        if not sesion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sesión no encontrada.",
            )

        self.prestamo_service.confirmar_prestamo(
            db,
            ConfirmarPrestamoRequest(
                sesion_id=sesion_id,
                equipo_id=request.equipo_id,
                accesorios=request.accesorios,
            ),
        )

        return AgregarEquipoManualResponse(
            sesion_id=sesion_id,
            equipo_id=request.equipo_id,
            mensaje="Equipo agregado manualmente y préstamo registrado.",
        )
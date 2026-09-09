from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.labtrack import Sesion
from app.repositories.estudiante_repository import EstudianteRepository
from app.repositories.sesion_repository import SesionRepository
from app.schemas.prestamo import ConfirmarPrestamoRequest
from app.schemas.sesion import (
    AbrirSesionManualResponse,
    AgregarEquipoManualRequest,
    AgregarEquipoManualResponse,
    CierreSesionResponse,
)
from app.services.prestamo_service import PrestamoService


class SesionService:
    def __init__(self) -> None:
        self.repo_sesion = SesionRepository()
        self.repo_estudiante = EstudianteRepository()
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
        estudiante_id: int,
    ) -> AbrirSesionManualResponse:
        """US-12: abre (o reutiliza) una sesión seleccionando al estudiante
        manualmente desde la web, sin depender del lector RFID.

        Reutiliza la misma regla de negocio que el flujo automático
        (app.services.identificaciones): si el estudiante ya tiene una
        sesión activa, se reutiliza; si no, se crea una nueva.
        """
        estudiante = self.repo_estudiante.get_by_id(db, estudiante_id)
        if not estudiante:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Estudiante no encontrado.",
            )

        sesion = self.repo_sesion.get_activa_by_estudiante(db, estudiante_id)
        if sesion:
            mensaje = "El estudiante ya tiene una sesión activa; se reutiliza."
        else:
            sesion = self.repo_sesion.create(db, estudiante_id)
            mensaje = "Sesión manual abierta correctamente."

        return AbrirSesionManualResponse(
            sesion_id=sesion.id,
            estudiante_id=estudiante_id,
            estado=sesion.estado,
            mensaje=mensaje,
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
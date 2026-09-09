""" Crear servicio de devolucion de equipos"""


from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.equipo_repository import EquipoRepository
from app.repositories.falla_repository import FallaRepository
from app.repositories.sesion_repository import SesionRepository
from app.schemas.devolucion import (
    AccesorioPrestadoInfo,
    ConfirmarDevolucionRequest,
    IniciarDevolucionManualRequest,
    IniciarDevolucionManualResponse,
    RegistrarFallaRequest,
    RegistrarFallaResponse,
)


class DevolucionService:
    
    def __init__(self)-> None:
        self.repo_sesion = SesionRepository()
        self.repo_equipo = EquipoRepository()
        self.repo_falla = FallaRepository()

    def confirmar_devolucion(
        self,
        db: Session,
        request: ConfirmarDevolucionRequest,
    ) -> dict[str, str]:
        """Registra la cantidad de accesorios devueltos de un préstamo."""

        # 1. Verificar que el préstamo exista
        prestamo = self.repo_sesion.get_sesion_equipo_by_id(
            db,
            request.sesion_equipo_id,
        )

        if not prestamo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Préstamo de equipo no encontrado.",
            )

        # 2. Procesar cada accesorio devuelto
        for accesorio_data in request.accesorios:
            accesorio = self.repo_sesion.get_accesorio_prestamo(
                db,
                request.sesion_equipo_id,
                accesorio_data.tipo_accesorio_id,
            )

            if not accesorio:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        "El accesorio no pertenece al préstamo "
                        "indicado."
                    ),
                )

            # 3. No permitir devolver más unidades de las prestadas
            if accesorio_data.cantidad_devuelta > accesorio.cantidad_prestada:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "La cantidad devuelta no puede ser mayor "
                        "a la cantidad prestada."
                    ),
                )

            # 4. Guardar la cantidad devuelta
            self.repo_sesion.actualizar_cantidad_devuelta(
                db,
                accesorio,
                accesorio_data.cantidad_devuelta,
            )

        return {
            "mensaje": "Devolución de accesorios registrada correctamente."
        }

    def registrar_falla(
        self,
        db: Session,
        sesion_equipo_id: int,
        request: RegistrarFallaRequest,
    ) -> RegistrarFallaResponse:
        """Registra si hubo o no una falla al devolver un equipo (US-08).

        Si hubo falla: se guarda en el historial del equipo y el equipo
        pasa a estado "En revisión".
        Si no hubo falla: el equipo pasa a estado "Disponible".
        Las fallas anteriores nunca se sobrescriben ni eliminan.
        """

        # 1. Verificar que el préstamo (devolución en curso) exista
        prestamo = self.repo_sesion.get_sesion_equipo_by_id(
            db,
            sesion_equipo_id,
        )

        if not prestamo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Préstamo de equipo no encontrado.",
            )

        equipo = prestamo.equipo

        if request.hubo_falla:
            # La validación de que 'descripcion' venga presente ya la
            # hace el schema (RegistrarFallaRequest), aquí solo persistimos.
            falla = self.repo_falla.create(
                db,
                equipo_id=equipo.id,
                sesion_equipo_id=prestamo.id,
                descripcion=request.descripcion,  # type: ignore[arg-type]
            )
            equipo = self.repo_equipo.actualizar_estado(db, equipo, "En revisión")

            return RegistrarFallaResponse(
                equipo_id=equipo.id,
                equipo_estado=equipo.estado,
                falla_id=falla.id,
                mensaje=(
                    "Falla registrada en el historial del equipo. "
                    "Equipo marcado como 'En revisión'."
                ),
            )

        equipo = self.repo_equipo.actualizar_estado(db, equipo, "Disponible")

        return RegistrarFallaResponse(
            equipo_id=equipo.id,
            equipo_estado=equipo.estado,
            falla_id=None,
            mensaje="Devolución sin fallas. Equipo marcado como 'Disponible'.",
        )

    def iniciar_devolucion_manual(
        self,
        db: Session,
        request: IniciarDevolucionManualRequest,
    ) -> IniciarDevolucionManualResponse:
        """US-12: inicia manualmente una devolución seleccionando el equipo
        desde la web (respaldo cuando el QR no está disponible).

        Reutiliza la misma consulta que usa el flujo automático por QR
        (SesionRepository.get_prestamo_activo_by_equipo) para ubicar el
        préstamo activo del equipo y devolver los datos necesarios para
        continuar con /api/devoluciones/accesorios y /falla.
        """
        if request.equipo_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Falta seleccionar un equipo para iniciar la devolución.",
            )

        equipo = self.repo_equipo.get_by_id(db, request.equipo_id)
        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Equipo no encontrado.",
            )

        if equipo.estado != "Prestado":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "El equipo no tiene un préstamo activo "
                    f"(estado actual: {equipo.estado})."
                ),
            )

        prestamo = self.repo_sesion.get_prestamo_activo_by_equipo(db, equipo.id)
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
            AccesorioPrestadoInfo(
                tipo_accesorio_id=acc.tipo_accesorio_id,
                nombre=acc.tipo_accesorio.nombre,
                cantidad_prestada=acc.cantidad_prestada,
            )
            for acc in prestamo.accesorios
        ]

        return IniciarDevolucionManualResponse(
            sesion_equipo_id=prestamo.id,
            equipo_id=equipo.id,
            codigo_equipo=equipo.codigo,
            estudiante_id=estudiante.id,
            estudiante_nombre=estudiante.nombre,
            accesorios=accesorios,
            mensaje="Devolución iniciada manualmente. Continúa con accesorios y falla.",
        )
import base64
from io import BytesIO
from typing import Any

import qrcode
from fastapi import HTTPException, status
from PIL.Image import Resampling
from qrcode.constants import ERROR_CORRECT_M
from qrcode.image.pil import PilImage
from sqlalchemy.orm import Session

from app.repositories.equipo_repository import EquipoRepository
from app.repositories.falla_repository import FallaRepository
from app.repositories.sesion_repository import SesionRepository
from app.schemas.equipo import (
    CambioEstadoEquipoRequest,
    CambioEstadoEquipoResponse,
    EquipoCreate,
    EquipoDetalleResponse,
    EquipoListItem,
    PrestamoActivoEquipoInfo,
)
from app.schemas.historial import (
    HistorialAccesorio,
    HistorialEquipoPrestamo,
    HistorialEquipoResponse,
    HistorialFalla,
)


class EquipoService:
    def __init__(self) -> None:
        self.repo = EquipoRepository()
        self.repo_sesion = SesionRepository()
        self.repo_falla = FallaRepository()

    def _generar_qr_data_uri(
        self, codigo: str, dpi: int = 300, tamano_cm: float = 4.0
    ) -> str:
        """Genera el QR del equipo a tamaño físico controlado (4x4cm por
        defecto), para que el sensor de la cámara del lector ESP32 pueda
        decodificarlo de forma consistente."""
        qr = qrcode.QRCode(
            version=1,  # sube esto si algún 'codigo' llega a ser más largo
            error_correction=ERROR_CORRECT_M,
            box_size=10,
            border=4,
            image_factory=PilImage,
        )
        qr.add_data(codigo)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        px_objetivo = int((tamano_cm / 2.54) * dpi)
        img = img.resize((px_objetivo, px_objetivo), Resampling.NEAREST)

        buffer = BytesIO()
        img.save(buffer, format="PNG", dpi=(dpi, dpi))
        qr_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{qr_b64}"

    def registrar_equipo(self, db: Session, equipo_in: EquipoCreate) -> dict[str, Any]:
        # 1. Verificar duplicados
        equipo_existente = self.repo.get_by_codigo(db, equipo_in.codigo)
        if equipo_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail="El dispositivo ya se encuentra registrado"
            )

        # 2. Buscar o crear tipo
        tipo = self.repo.get_tipo_by_nombre(db, equipo_in.tipo)
        if not tipo:
            tipo = self.repo.create_tipo(db, equipo_in.tipo)

        # 3. Crear equipo físico
        nuevo_equipo = self.repo.create(db, equipo_in.codigo, tipo.id)

        # 4. Generar el código QR en memoria (Base64)
        qr_data_uri = self._generar_qr_data_uri(nuevo_equipo.codigo)

        # 5. Devolver los datos
        return {
            "id": nuevo_equipo.id,
            "codigo": nuevo_equipo.codigo,
            "estado": nuevo_equipo.estado,
            "tipo": tipo.nombre,
            "qr_base64": qr_data_uri
        }


    def listar(
        self,
        db: Session,
        codigo: str | None = None,
        estado: str | None = None,
        tipo: str | None = None,
    ) -> list[EquipoListItem]:
        """Lista/busca equipos (GET /api/equipos)."""
        equipos = self.repo.search(db, codigo=codigo, estado=estado, tipo=tipo)
        return [
            EquipoListItem(
                codigo=e.codigo,
                tipo=e.tipo_equipo.nombre,
                estado=e.estado,
            )
            for e in equipos
        ]

    def obtener_detalle(self, db: Session, codigo: str) -> EquipoDetalleResponse:
        """Detalle de un equipo identificado por su código QR
        (GET /api/equipos/{codigo})."""
        equipo = self.repo.get_by_codigo(db, codigo)
        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Equipo con código '{codigo}' no encontrado.",
            )

        prestamo_activo = None
        if equipo.estado == "Prestado":
            prestamo = self.repo_sesion.get_prestamo_activo_by_equipo(db, equipo.id)
            if prestamo:
                estudiante = prestamo.sesion.estudiante
                prestamo_activo = PrestamoActivoEquipoInfo(
                    matricula=estudiante.matricula,
                    estudiante_nombre=estudiante.nombre,
                    fecha_prestamo=prestamo.fecha_prestamo,
                )

        fallas = self.repo_falla.get_by_equipo(db, equipo.id)

        return EquipoDetalleResponse(
            codigo=equipo.codigo,
            tipo=equipo.tipo_equipo.nombre,
            estado=equipo.estado,
            prestamo_activo=prestamo_activo,
            fallas=[
                HistorialFalla(
                    id=f.id,
                    descripcion=f.descripcion,
                    estado=f.estado,
                    fecha=f.fecha,
                )
                for f in fallas
            ],
        )

    def obtener_historial(self, db: Session, codigo: str) -> HistorialEquipoResponse:
        """Historial completo de préstamos de un equipo, identificado por
        su código QR (US-10). Ordenado por fecha de préstamo, más
        reciente primero (ya viene ordenado desde el repository)."""
        equipo = self.repo.get_by_codigo(db, codigo)
        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Equipo con código '{codigo}' no encontrado.",
            )

        prestamos_bd = self.repo_sesion.get_historial_by_equipo(db, equipo.id)

        prestamos = [
            HistorialEquipoPrestamo(
                matricula=prestamo.sesion.estudiante.matricula,
                estudiante_nombre=prestamo.sesion.estudiante.nombre,
                estado_prestamo=prestamo.estado,
                fecha_prestamo=prestamo.fecha_prestamo,
                fecha_devolucion=prestamo.fecha_devolucion,
                accesorios=[
                    HistorialAccesorio(
                        nombre=acc.tipo_accesorio.nombre,
                        cantidad_prestada=acc.cantidad_prestada,
                        cantidad_devuelta=acc.cantidad_devuelta,
                    )
                    for acc in prestamo.accesorios
                ],
                fallas=[
                    HistorialFalla(
                        id=f.id,
                        descripcion=f.descripcion,
                        estado=f.estado,
                        fecha=f.fecha,
                    )
                    for f in prestamo.fallas
                ],
            )
            for prestamo in prestamos_bd
        ]

        return HistorialEquipoResponse(
            codigo=equipo.codigo,
            tipo=equipo.tipo_equipo.nombre,
            estado=equipo.estado,
            prestamos=prestamos,
        )

    def cambiar_estado(
        self,
        db: Session,
        codigo: str,
        request: CambioEstadoEquipoRequest,
    ) -> CambioEstadoEquipoResponse:
        """Cambia manualmente el estado de un equipo desde la pantalla de
        detalle (identificado por su código QR).

        Reutiliza la misma lógica de negocio que US-08
        (DevolucionService.registrar_falla): si hubo falla, se registra en
        el historial del equipo y este pasa a 'En revisión'; si no, pasa a
        'Disponible'.

        Nota de trazabilidad: cuando `hubo_falla` es falso, la
        `observacion` recibida (si la hay) NO se persiste en base de
        datos porque el proyecto no cuenta con un mecanismo de auditoría
        de cambios de estado; solo se refleja en el mensaje de respuesta.
        """
        equipo = self.repo.get_by_codigo(db, codigo)
        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Equipo con código '{codigo}' no encontrado.",
            )

        if request.hubo_falla:
            falla = self.repo_falla.create(
                db,
                equipo_id=equipo.id,
                sesion_equipo_id=None,
                descripcion=request.descripcion,  # type: ignore[arg-type]
            )
            equipo = self.repo.actualizar_estado(db, equipo, "En revisión")
            return CambioEstadoEquipoResponse(
                codigo=equipo.codigo,
                estado=equipo.estado,
                falla_id=falla.id,
                mensaje=(
                    "Falla registrada en el historial del equipo. "
                    "Equipo marcado como 'En revisión'."
                ),
            )

        equipo = self.repo.actualizar_estado(db, equipo, "Disponible")
        mensaje = "Equipo marcado como 'Disponible'."
        if request.observacion:
            mensaje += " Observación recibida (no persistida): " + request.observacion

        return CambioEstadoEquipoResponse(
            codigo=equipo.codigo,
            estado=equipo.estado,
            falla_id=None,
            mensaje=mensaje,
        )
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.historial import HistorialFalla


class EquipoBase(BaseModel):
    codigo: str = Field(..., description="Código único físico del equipo")
    tipo: str = Field(..., description="Clasificación del equipo")

class EquipoCreate(EquipoBase):
    """Esquema para la creación del equipo."""
    pass

class EquipoOut(BaseModel):
    """Esquema de respuesta de la API."""
    id: int
    codigo: str
    estado: str
    tipo: str
    qr_base64: str | None = None 

    model_config = ConfigDict(from_attributes=True)


class EquipoListItem(BaseModel):
    """Elemento de la lista de equipos (GET /api/equipos).

    La interfaz debe operar con `codigo` (el valor del QR), no con el id
    interno.
    """

    codigo: str
    tipo: str
    estado: str


class PrestamoActivoEquipoInfo(BaseModel):
    """Resumen del préstamo activo de un equipo, para la vista de detalle."""

    matricula: str
    estudiante_nombre: str
    fecha_prestamo: datetime


class EquipoDetalleResponse(BaseModel):
    """Respuesta de GET /api/equipos/{codigo}: información necesaria para
    la pantalla de detalle de un equipo, identificado por su código QR."""

    codigo: str
    tipo: str
    estado: str
    prestamo_activo: PrestamoActivoEquipoInfo | None = None
    fallas: list[HistorialFalla] = []


class CambioEstadoEquipoRequest(BaseModel):
    """Payload para el cambio manual de estado de un equipo desde la
    pantalla de detalle (¿hubo falla o no?)."""

    hubo_falla: bool
    descripcion: str | None = Field(default=None, max_length=1000)
    observacion: str | None = Field(
        default=None,
        max_length=1000,
        description=(
            "Motivo del cambio cuando no hubo falla. No se persiste en "
            "base de datos: el proyecto no cuenta con un mecanismo de "
            "auditoría de cambios de estado; solo se usa para el mensaje "
            "de confirmación."
        ),
    )

    @model_validator(mode="after")
    def validar_descripcion_si_hay_falla(self) -> "CambioEstadoEquipoRequest":
        if self.hubo_falla and not (self.descripcion and self.descripcion.strip()):
            raise ValueError(
                "Se requiere una descripción cuando 'hubo_falla' es verdadero."
            )
        return self


class CambioEstadoEquipoResponse(BaseModel):
    codigo: str
    estado: str
    falla_id: int | None = None
    mensaje: str
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.schemas.historial import HistorialFalla


class EquipoBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    codigo: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Código del laboratorio (ej. OSC-0330). Es el valor del QR.",
    )
    tipo: str = Field(
        ..., min_length=1, max_length=100, description="Clasificación del equipo"
    )


class EquipoCreate(EquipoBase):
    """Esquema para la creación del equipo."""

    numero_inventario: str | None = Field(
        default=None,
        max_length=50,
        description="Número oficial de inventario (distinto del código del lab).",
    )
    marca: str | None = Field(default=None, max_length=100)
    modelo: str | None = Field(default=None, max_length=100)

    @field_validator("numero_inventario", "marca", "modelo")
    @classmethod
    def vacio_a_none(cls, valor: str | None) -> str | None:
        return valor or None

class EquipoOut(BaseModel):
    """Esquema de respuesta de la API."""
    id: int
    codigo: str
    estado: str
    tipo: str
    numero_inventario: str | None = None
    marca: str | None = None
    modelo: str | None = None
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
    numero_inventario: str | None = None
    marca: str | None = None
    modelo: str | None = None


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
    numero_inventario: str | None = None
    marca: str | None = None
    modelo: str | None = None
    qr_base64: str
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


class EquipoUpdate(BaseModel):
    """Payload para PUT /api/equipos/{codigo}.

    Solo permite corregir el `tipo`. El `codigo` no es editable a
    propósito: es el mismo valor codificado en el QR físico ya pegado
    al equipo, así que cambiarlo por API dejaría la etiqueta impresa
    desincronizada con la base de datos.
    """

    tipo: str = Field(..., description="Clasificación corregida del equipo")


class BajaEquipoResponse(BaseModel):
    """Respuesta de PATCH /api/equipos/{codigo}/baja."""

    codigo: str
    estado: str
    mensaje: str


class ResumenEquipos(BaseModel):
    """Conteo de equipos por estado (GET /api/equipos/resumen).

    Cada equipo tiene un único estado, así que
    total == disponibles + prestados + en_revision + baja + otros.
    """

    total: int
    disponibles: int
    prestados: int
    en_revision: int
    baja: int
    otros: int = 0

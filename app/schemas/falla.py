from datetime import datetime

from pydantic import BaseModel, Field


class FallaListItem(BaseModel):
    """Elemento de GET /api/fallas.

    Identifica el equipo por su código QR, no por su id interno.
    """

    id: int
    codigo_equipo: str
    tipo_equipo: str
    descripcion: str
    fecha: datetime
    estado: str
    matricula: str | None = None
    estudiante_nombre: str | None = None
    fecha_resolucion: datetime | None = None
    observacion_resolucion: str | None = None


class FallaDetalleResponse(BaseModel):
    """Respuesta de GET /api/fallas/{id}."""

    id: int
    codigo_equipo: str
    tipo_equipo: str
    descripcion: str
    fecha: datetime
    estado: str
    matricula: str | None = None
    estudiante_nombre: str | None = None
    fecha_resolucion: datetime | None = None
    observacion_resolucion: str | None = None


class ResolverFallaRequest(BaseModel):
    """Payload para PATCH /api/fallas/{falla_id}/resolver."""

    observacion_resolucion: str | None = Field(default=None, max_length=1000)


class ResolverFallaResponse(BaseModel):
    """Respuesta de PATCH /api/fallas/{falla_id}/resolver.

    Incluye el estado resultante del equipo porque resolver la falla
    puede hacerlo salir de 'En revisión'.
    """

    falla_id: int
    equipo_id: int
    codigo_equipo: str
    equipo_estado: str
    mensaje: str

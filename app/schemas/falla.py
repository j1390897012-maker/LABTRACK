from datetime import datetime

from pydantic import BaseModel


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

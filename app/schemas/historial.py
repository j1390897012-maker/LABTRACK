from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HistorialFalla(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha: datetime

class HistorialAccesorio(BaseModel):
    nombre: str
    cantidad_prestada: int
    cantidad_devuelta: int | None

class HistorialEquipo(BaseModel):
    codigo: str
    tipo: str
    estado_prestamo: str  # "Prestado", "Devuelto", etc.
    fecha_prestamo: datetime
    fecha_devolucion: datetime | None
    accesorios: list[HistorialAccesorio] = []
    fallas: list[HistorialFalla] = []

class HistorialSesion(BaseModel):
    sesion_id: int
    estado: str  # "Activa", "Cerrada"
    fecha_apertura: datetime
    fecha_cierre: datetime | None
    equipos: list[HistorialEquipo] = []

class HistorialEstudianteResponse(BaseModel):
    estudiante_id: int
    nombre: str
    matricula: str
    sesiones: list[HistorialSesion] = []

model_config = ConfigDict(from_attributes=True)


class HistorialEquipoPrestamo(BaseModel):
    """Un préstamo individual dentro del historial de un equipo (US-10)."""

    matricula: str
    estudiante_nombre: str
    estado_prestamo: str  # "Prestado", "Devuelto", etc.
    fecha_prestamo: datetime
    fecha_devolucion: datetime | None
    accesorios: list[HistorialAccesorio] = []
    fallas: list[HistorialFalla] = []


class HistorialEquipoResponse(BaseModel):
    """Respuesta de GET /api/equipos/{codigo}/historial.

    El equipo se identifica por su código QR, no por su id interno.
    Los préstamos se devuelven ordenados por fecha de préstamo,
    más reciente primero.
    """

    codigo: str
    tipo: str
    estado: str
    prestamos: list[HistorialEquipoPrestamo] = []
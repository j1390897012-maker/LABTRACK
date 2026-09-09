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
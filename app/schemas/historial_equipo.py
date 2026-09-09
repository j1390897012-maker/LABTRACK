from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HistorialFallaEquipo(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha: datetime

class HistorialUsoEquipo(BaseModel):
    sesion_equipo_id: int
    estudiante_nombre: str
    matricula_estudiante: str
    estado_prestamo: str
    fecha_prestamo: datetime
    fecha_devolucion: datetime | None
    fallas: list[HistorialFallaEquipo] = []

class HistorialEquipoResponse(BaseModel):
    equipo_id: int
    codigo: str
    tipo: str
    estado_actual: str
    historial_usos: list[HistorialUsoEquipo] = []

    model_config = ConfigDict(from_attributes=True)
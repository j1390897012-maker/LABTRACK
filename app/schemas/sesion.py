from pydantic import BaseModel, Field

from app.schemas.prestamo import AccesorioPrestamoCreate


class CierreSesionResponse(BaseModel):
    sesion_id: int
    estado: str
    mensaje: str
    equipos_prestados: int


class AbrirSesionManualRequest(BaseModel):
    """US-12: abrir manualmente una sesión seleccionando al estudiante."""

    estudiante_id: int


class AbrirSesionManualResponse(BaseModel):
    sesion_id: int
    estudiante_id: int
    estado: str
    mensaje: str


class AgregarEquipoManualRequest(BaseModel):
    """US-12: agregar manualmente un equipo a una sesión.

    equipo_id es opcional a nivel de schema para poder devolver un mensaje
    de negocio claro ("falta seleccionar un equipo") en vez del 422
    genérico de Pydantic.
    """

    equipo_id: int | None = Field(default=None)
    accesorios: list[AccesorioPrestamoCreate] = []


class AgregarEquipoManualResponse(BaseModel):
    sesion_id: int
    equipo_id: int
    mensaje: str

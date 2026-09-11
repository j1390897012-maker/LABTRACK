from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.schemas.prestamo import AccesorioPrestamoCreate


class CierreSesionResponse(BaseModel):
    sesion_id: int
    estado: str
    mensaje: str
    equipos_prestados: int


class AbrirSesionManualRequest(BaseModel):
    """US-12: abrir manualmente una sesión seleccionando al estudiante.

    La interfaz debe operar con `matricula`; `estudiante_id` se conserva
    únicamente por compatibilidad con integraciones internas existentes.
    """

    estudiante_id: int | None = None
    matricula: str | None = None

    @model_validator(mode="after")
    def validar_identificador(self) -> "AbrirSesionManualRequest":
        if self.estudiante_id is None and not self.matricula:
            raise ValueError(
                "Debe indicar 'matricula' (o, en su defecto, 'estudiante_id')."
            )
        return self


class AbrirSesionManualResponse(BaseModel):
    sesion_id: int
    estudiante_id: int
    matricula: str
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


class EquipoActivoInfo(BaseModel):
    """Un equipo actualmente prestado dentro de una sesión activa."""

    codigo: str
    tipo: str
    fecha_prestamo: datetime


class SesionActivaResponse(BaseModel):
    """Respuesta de GET /api/sesiones/activa?matricula=...

    La interfaz consulta usando la matrícula del estudiante, no su id
    interno.
    """

    sesion_id: int
    estudiante_id: int
    matricula: str
    estado: str
    equipos: list[EquipoActivoInfo] = []


class PrestamoManualRequest(BaseModel):
    """US-12: registra en un solo paso un préstamo manual usando la
    matrícula del estudiante y el código QR del equipo.

    Abre (o reutiliza) la sesión del estudiante y registra el préstamo del
    equipo, reutilizando la misma lógica de negocio que el flujo por
    RFID/QR y el flujo manual de dos pasos.
    """

    matricula: str
    codigo_equipo: str
    accesorios: list[AccesorioPrestamoCreate] = []


class PrestamoManualResponse(BaseModel):
    sesion_id: int
    matricula: str
    codigo_equipo: str
    mensaje: str

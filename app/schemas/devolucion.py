from pydantic import BaseModel, Field, model_validator


class AccesorioDevuelto(BaseModel):
    tipo_accesorio_id: int
    cantidad_devuelta: int = Field(ge=0)



class ConfirmarDevolucionRequest(BaseModel):
    sesion_equipo_id: int 
    accesorios: list[AccesorioDevuelto]


class RegistrarFallaRequest(BaseModel):
    """Payload para registrar (o descartar) una falla al devolver un equipo (US-08)."""

    hubo_falla: bool
    descripcion: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validar_descripcion_si_hay_falla(self) -> "RegistrarFallaRequest":
        if self.hubo_falla and not (self.descripcion and self.descripcion.strip()):
            raise ValueError(
                "Se requiere una descripción cuando 'hubo_falla' es verdadero."
            )
        return self


class RegistrarFallaResponse(BaseModel):
    equipo_id: int
    equipo_estado: str
    falla_id: int | None = None
    mensaje: str


class IniciarDevolucionManualRequest(BaseModel):
    """US-12: iniciar manualmente una devolución seleccionando el equipo."""

    equipo_id: int | None = Field(default=None)


class AccesorioPrestadoInfo(BaseModel):
    tipo_accesorio_id: int
    nombre: str
    cantidad_prestada: int


class IniciarDevolucionManualResponse(BaseModel):
    sesion_equipo_id: int
    equipo_id: int
    codigo_equipo: str
    estudiante_id: int
    estudiante_nombre: str
    accesorios: list[AccesorioPrestadoInfo] = []
    mensaje: str


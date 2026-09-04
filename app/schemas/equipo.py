from pydantic import BaseModel, ConfigDict, Field


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
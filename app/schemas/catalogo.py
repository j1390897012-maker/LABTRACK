from pydantic import BaseModel, ConfigDict


class TipoEquipoOut(BaseModel):
    """Elemento del catálogo de tipos de equipo (GET /api/tipos-equipo)."""

    id: int
    nombre: str

    model_config = ConfigDict(from_attributes=True)


class TipoAccesorioOut(BaseModel):
    """Elemento del catálogo de tipos de accesorio
    (GET /api/tipos-accesorio)."""

    id: int
    nombre: str
    cantidad_default: int
    tipo_equipo_id: int

    model_config = ConfigDict(from_attributes=True)

from pydantic import BaseModel, Field


class AccesorioDevuelto(BaseModel):
    tipo_accesorio_id: int
    cantidad_devuelta: int = Field(ge=0)



class ConfirmarDevolucionRequest(BaseModel):
    sesion_equipo_id: int 
    accesorios: list[AccesorioDevuelto]

    
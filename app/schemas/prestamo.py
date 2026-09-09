from pydantic import BaseModel, Field


class AccesorioPrestamoCreate(BaseModel):
    tipo_accesorio_id: int
    cantidad: int = Field(gt=0, description="La cantidad debe ser mayor a 0")

class ConfirmarPrestamoRequest(BaseModel):
    sesion_id: int
    equipo_id: int
    accesorios: list[AccesorioPrestamoCreate] = []
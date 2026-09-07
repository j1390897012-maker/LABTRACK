from pydantic import BaseModel


class AccesorioPrestamoCreate(BaseModel):
    tipo_accesorio_id: int
    cantidad: int

class ConfirmarPrestamoRequest(BaseModel):
    sesion_id: int
    equipo_id: int
    accesorios: list[AccesorioPrestamoCreate] = []
from pydantic import BaseModel


class CierreSesionResponse(BaseModel):
    sesion_id: int
    estado: str
    mensaje: str
    equipos_prestados: int
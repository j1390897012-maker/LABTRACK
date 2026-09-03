from pydantic import BaseModel


class IdentificacionResponse(BaseModel):
    """ Modelo para representar la respuesta de la identificación """
    estudiante_id: int |None
    nombre: str |None
    matricula: str |None
    uid_rfid: str 
    estado: str # "registrado | no_registrado" | "error"
    mensaje: str


class AsignacionRFIDRequest(BaseModel):
    """ Modelo para representar la solicitud de enrolar una tarjeta"""
    tipo: str
    valor: str
    estudiante_id: int


class AsignacionRFIDResponse(BaseModel):
    """ Modelo para representar la respuesta de la asignación de RFID """
    estudiante_id: int
    nombre: str
    matricula: str
    uid_rfid: str
    mensaje: str 
    



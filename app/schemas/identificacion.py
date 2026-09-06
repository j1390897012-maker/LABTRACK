
from pydantic import BaseModel


class ScanRequest(BaseModel):
    """ Modelo para recibir la petición del ESP32 """
    tipo: str
    valor: str
    lector_id: str | None = None
    sesion_id: int | None = None

class AccesorioInfo(BaseModel):
    id: int
    nombre: str
    cantidad_default: int

class QRScanResponse(BaseModel):
    """ Modelo de respuesta al escanear un equipo vía QR """
    tipo: str = "equipo"
    equipo_id: int
    codigo: str
    estado: str
    mensaje: str
    accesorios: list[AccesorioInfo] = []

class IdentificacionResponse(BaseModel):
    """ Modelo para representar la respuesta de la identificación """
    tipo: str = "estudiante"
    estudiante_id: int | None = None
    nombre: str | None = None
    matricula: str | None = None
    uid_rfid: str
    estado: str 
    mensaje: str
    accion: str | None = None
    sesion_id: int | None = None
    equipos_actuales: list[str] = []

class AsignacionRFIDRequest(BaseModel):
    """ Modelo para representar la solicitud de enrolar una tarjeta"""
    tipo: str
    valor: str
    matricula: str

class AsignacionRFIDResponse(BaseModel):
    """ Modelo para representar la respuesta de la asignación de RFID """
    estudiante_id: int
    nombre: str
    matricula: str
    uid_rfid: str
    mensaje: str
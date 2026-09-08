from app.routers.devolucion import router as devolucion_router
from app.routers.equipo import router as equipo
from app.routers.estudiante import router as estudiante
from app.routers.identificaciones import router as identificaciones

__all__ = [
    "devolucion_router",
    "equipo",
    "estudiante",
    "identificaciones",
]
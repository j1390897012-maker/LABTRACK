from app.routers.catalogos import router as catalogos
from app.routers.devolucion import router as devolucion_router
from app.routers.equipo import router as equipo
from app.routers.estudiante import router as estudiante
from app.routers.fallas import router as fallas
from app.routers.identificaciones import router as identificaciones

__all__ = [
    "catalogos",
    "devolucion_router",
    "equipo",
    "estudiante",
    "fallas",
    "identificaciones",
]
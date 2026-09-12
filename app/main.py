from fastapi import FastAPI

from app.routers import (
    catalogos,
    devolucion_router,
    equipo,
    estudiante,
    fallas,
    identificaciones,
)
from app.routers.sesiones import router as sesiones_router

app = FastAPI(title="LABTRACK")

app.include_router(equipo)
app.include_router(identificaciones)
app.include_router(estudiante)
app.include_router(devolucion_router)
app.include_router(sesiones_router)
app.include_router(catalogos)
app.include_router(fallas)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
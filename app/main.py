from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import (
    catalogos,
    devolucion_router,
    equipo,
    estudiante,
    fallas,
    historial,
    identificaciones,
)
from app.routers.sesiones import router as sesiones_router

app = FastAPI(title="LABTRACK")

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(equipo)
app.include_router(identificaciones)
app.include_router(estudiante)
app.include_router(devolucion_router)
app.include_router(sesiones_router)
app.include_router(catalogos)
app.include_router(fallas)
app.include_router(historial)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

# Servir la interfaz web estática en la raíz (debe ir estrictamente al final)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
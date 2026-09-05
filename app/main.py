from fastapi import FastAPI

from app.routers import (  # <-- 1. Importas tu router
    equipo,
    estudiante,
    identificaciones,
)

app = FastAPI(title="LABTRACK")
app.include_router(equipo.router)
app.include_router(identificaciones.router)
app.include_router(estudiante.router)  # <-- 2. Incluyes tu router en la aplicación

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

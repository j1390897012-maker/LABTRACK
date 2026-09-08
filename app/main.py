from fastapi import FastAPI

from app.routers import (
    devolucion_router,
    equipo,
    estudiante,
    identificaciones,
)

app = FastAPI(title="LABTRACK")

app.include_router(equipo)
app.include_router(identificaciones)
app.include_router(estudiante)
app.include_router(devolucion_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
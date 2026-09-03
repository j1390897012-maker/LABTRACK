from fastapi import FastAPI

from app.routers import equipo, identificaciones  # <-- 1. Importas tu router

app = FastAPI(title="LABTRACK")
app.include_router(equipo.router)
app.include_router(identificaciones.router)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

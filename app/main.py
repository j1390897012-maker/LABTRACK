from fastapi import FastAPI

from app.routers import equipo  # <-- 1. Importas tu router

app = FastAPI(title="LABTRACK")
app.include_router(equipo.router)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

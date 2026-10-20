from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.realtime import METODOS_ESCRITURA, manager, mensaje_de_cambio
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

@app.middleware("http")
async def avisar_cambios(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Tras cualquier escritura exitosa en /api/*, avisa a los paneles
    abiertos por WebSocket para que se actualicen sin recargar."""
    respuesta = await call_next(request)
    ruta = request.url.path
    if (
        request.method in METODOS_ESCRITURA
        and ruta.startswith("/api/")
        and respuesta.status_code < 400
    ):
        await manager.difundir(mensaje_de_cambio(request.method, ruta))
    return respuesta


@app.websocket("/ws")
async def websocket_eventos(ws: WebSocket) -> None:
    """Canal de avisos para el panel. El cliente puede enviar 'ping' y
    recibe 'pong' (sirve para detectar conexiones caídas)."""
    await manager.conectar(ws)
    try:
        while True:
            if await ws.receive_text() == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        manager.desconectar(ws)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

# Servir la interfaz web estática en la raíz (debe ir estrictamente al final)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
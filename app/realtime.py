"""Notificaciones en tiempo real por WebSocket.

El panel web mantiene una conexión a /ws. Cada vez que una petición de
escritura a /api/* termina bien (desde el panel, la app Android o el
script de carga), se avisa a todos los paneles abiertos con un mensaje
{"evento": "cambio", "recurso": "...", ...} y ellos vuelven a pedir sus
datos. No se envían datos sensibles por el socket: solo el aviso.

Limitación conocida: el gestor vive en memoria del proceso, por lo que
funciona con un solo worker de uvicorn (como está en el Dockerfile).
"""

import asyncio
import contextlib
import logging
from datetime import UTC, datetime

from fastapi import WebSocket

logger = logging.getLogger("labtrack.realtime")

METODOS_ESCRITURA = {"POST", "PUT", "PATCH", "DELETE"}


class ConnectionManager:
    def __init__(self) -> None:
        self._conexiones: set[WebSocket] = set()

    @property
    def total(self) -> int:
        return len(self._conexiones)

    async def conectar(self, ws: WebSocket) -> None:
        await ws.accept()
        self._conexiones.add(ws)

    def desconectar(self, ws: WebSocket) -> None:
        self._conexiones.discard(ws)

    async def difundir(self, mensaje: dict[str, object]) -> None:
        """Envía el mensaje a todos; descarta las conexiones rotas."""
        if not self._conexiones:
            return
        muertas: list[WebSocket] = []
        resultados = await asyncio.gather(
            *(c.send_json(mensaje) for c in list(self._conexiones)),
            return_exceptions=True,
        )
        for conexion, resultado in zip(
            list(self._conexiones), resultados, strict=True
        ):
            if isinstance(resultado, Exception):
                muertas.append(conexion)
        for conexion in muertas:
            self.desconectar(conexion)
            with contextlib.suppress(Exception):
                await conexion.close()


manager = ConnectionManager()


def recurso_de_ruta(ruta: str) -> str:
    """'/api/equipos/OSC-1/baja' -> 'equipos'."""
    partes = [p for p in ruta.split("/") if p]
    return partes[1] if len(partes) > 1 and partes[0] == "api" else ""


def mensaje_de_cambio(metodo: str, ruta: str) -> dict[str, object]:
    return {
        "evento": "cambio",
        "recurso": recurso_de_ruta(ruta),
        "metodo": metodo,
        "ruta": ruta,
        "hora": datetime.now(UTC).isoformat(),
    }

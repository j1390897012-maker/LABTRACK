"""Esquemas de la importación masiva por archivo (equipos y estudiantes)."""

from pydantic import BaseModel


class ErrorFila(BaseModel):
    fila: int  # número de fila tal como se ve en Excel (el encabezado es la 1)
    valor: str | None = None  # código o matrícula de la fila, si se pudo leer
    motivo: str


class ImportacionResponse(BaseModel):
    """Resultado de POST /api/equipos/importar y /api/estudiantes/importar.

    La carga es todo-o-nada: si `errores` trae algo, no se guardó nada
    (`aplicado` = False) y se corrige el archivo completo.
    """

    total_filas: int
    creados: int
    actualizados: int
    fallas_creadas: int = 0
    errores: list[ErrorFila]
    aplicado: bool
    dry_run: bool

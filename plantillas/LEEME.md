# Plantillas de carga masiva

**Equipos** (`plantilla_equipos.xlsx`) — columnas:
| columna | obligatoria | notas |
|---|---|---|
| `codigo` | sí | Inventario del laboratorio (ej. OSC0330). Es el valor del QR. |
| `numero_inventario` | no | Inventario institucional; no se puede repetir. |
| `marca`, `modelo` | no | |
| `tipo` | no | Si falta, se usa "Sin clasificar". |
| `estado` | no | Disponible, En revisión o Baja. Vacío = Disponible. |

**Estudiantes** (`plantilla_estudiantes.xlsx`): `matricula` y `nombre`, ambas obligatorias.

Reglas: se acepta .xlsx o .csv (coma o punto y coma); todo-o-nada (si una fila falla no se guarda nada);
volver a subir el archivo actualiza lo existente, no duplica; usa `?dry_run=true` para solo validar.

## Hoja de inventario del laboratorio (`inventario_laboratorio.xlsx`)
Se importa tal cual (se lee la primera hoja). Columnas usadas: Equipo → tipo, Código lab → codigo,
Marca, Modelo, N° inventario, Estado. Se ignoran #, Año, Observaciones y Fecha, y las filas vacías.
Estados: Funciona bien → Disponible; Funciona parcialmente, No funciona y Sin revisar → En revisión.

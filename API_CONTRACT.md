# Borrador del contrato de API — LABTRACK

> **Estado:** Borrador — Compuerta 1
> **Versión:** 0.1
> **Propósito:** Definir las operaciones principales de la API del MVP antes de su implementación.

## 1. Objetivo

LABTRACK contará con una API REST para gestionar el préstamo, devolución y seguimiento de equipos de laboratorio.

La API será utilizada principalmente por la interfaz web del encargado y por el dispositivo ESP32 encargado de leer las tarjetas y etiquetas RFID.

El contrato define las operaciones principales necesarias para implementar el flujo del MVP. Los schemas detallados, validaciones específicas y respuestas definitivas podrán ajustarse durante la etapa de construcción.

---

# 2. Estudiantes

| Método | Endpoint                          | Descripción                                              | US relacionada |
| ------ | --------------------------------- | -------------------------------------------------------- | -------------- |
| `POST` | `/api/estudiantes`                | Registrar un estudiante con nombre y matrícula.          | —              |
| `GET`  | `/api/estudiantes/{id}`           | Consultar los datos de un estudiante.                    | —              |
| `GET`  | `/api/estudiantes/{id}/historial` | Consultar el historial de préstamos del estudiante.      | US-11          |
| `GET`  | `/api/estudiantes/{id}/actuales`  | Consultar los equipos que tiene actualmente en préstamo. | US-11          |

---

# 3. Equipos

| Método  | Endpoint                       | Descripción                                                           | US relacionada |
| ------- | ------------------------------ | --------------------------------------------------------------------- | -------------- |
| `POST`  | `/api/equipos`                 | Registrar un equipo con código y tipo.                                | US-01          |
| `GET`   | `/api/equipos/{codigo}`        | Consultar la ficha del equipo, incluyendo estado, fallas e historial. | US-10          |
| `GET`   | `/api/equipos`                 | Listar equipos, con filtro opcional por estado.                       | —              |
| `PATCH` | `/api/equipos/{codigo}/estado` | Cambiar manualmente el estado de un equipo.                           | US-08          |

Estados principales de un equipo:

* `Disponible`
* `Prestado`
* `En revisión`

---

# 4. RFID e identificación

El ESP32 enviará a la API el UID de la tarjeta o etiqueta RFID detectada.

La API será responsable de determinar si el UID corresponde a un estudiante o a un equipo y de ejecutar la acción correspondiente según el contexto actual.

| Método | Endpoint            | Descripción                                                | US relacionada      |
| ------ | ------------------- | ---------------------------------------------------------- | ------------------- |
| `POST` | `/api/rfid/scan`    | Recibir un UID leído por el ESP32 y resolver su identidad. | US-02, US-03, US-06 |
| `POST` | `/api/rfid/enrolar` | Asociar un UID RFID a un estudiante o equipo.              | US-09               |

### POST `/api/rfid/scan`

#### Request

```json
{
  "uid": "A1B2C3D4",
  "lector_id": "esp32-mesa-1"
}
```

#### Ejemplo: RFID de estudiante

Cuando se escanea la credencial de un estudiante, el sistema identifica al estudiante y abre automáticamente un pedido activo para él.

```json
{
  "tipo": "estudiante",
  "estudiante_id": 15,
  "nombre": "Alberto",
  "accion": "pedido_abierto",
  "pedido_id": 42,
  "equipos_actuales": []
}
```

#### Ejemplo: RFID de equipo durante un pedido

Cuando existe un pedido activo para el estudiante y se escanea un equipo disponible, este se agrega automáticamente al pedido.

```json
{
  "tipo": "equipo",
  "codigo": "OSC-0307",
  "accion": "agregado_a_pedido",
  "pedido_id": 42,
  "accesorios_sugeridos": [
    {
      "nombre": "Puntas para osciloscopio",
      "cantidad_default": 2
    }
  ]
}
```

#### Ejemplo: RFID de equipo prestado

Cuando se escanea un equipo que ya está prestado, la API identifica al estudiante que lo tiene y permite iniciar su devolución.

```json
{
  "tipo": "equipo",
  "codigo": "OSC-0307",
  "accion": "devolucion_iniciada",
  "pedido_id": 42,
  "estudiante": {
    "id": 15,
    "nombre": "Alberto"
  }
}
```

---

# 5. Pedidos de préstamo

Un pedido representa la operación de entrega de uno o varios equipos a un estudiante.

El flujo está diseñado para que el encargado pueda escanear varios equipos consecutivamente sin tener que confirmar cada uno individualmente.

| Método | Endpoint                                           | Descripción                                                   | US relacionada |
| ------ | -------------------------------------------------- | ------------------------------------------------------------- | -------------- |
| `POST` | `/api/pedidos`                                     | Abrir un pedido para un estudiante mediante selección manual. | US-02, US-12   |
| `POST` | `/api/pedidos/{id}/equipos`                        | Agregar manualmente un equipo a un pedido.                    | US-03, US-12   |
| `PUT`  | `/api/pedidos/{id}/equipos/{equipo_id}/accesorios` | Registrar la cantidad de accesorios entregados con un equipo. | US-04          |
| `POST` | `/api/pedidos/{id}/cerrar`                         | Cerrar el pedido y marcar los equipos como prestados.         | US-05          |
| `GET`  | `/api/pedidos/activos?estudiante_id={id}`          | Consultar el pedido activo de un estudiante.                  | US-02          |

---

# 6. Accesorios

Los accesorios se registran asociados al préstamo del equipo.

El sistema permitirá indicar cantidades diferentes dependiendo del tipo de equipo.

Ejemplos:

* Osciloscopio → puntas de osciloscopio.
* Generador → puntas o cables correspondientes.
* Fuente → cables de alimentación o conexión.

La cantidad será introducida por el encargado durante el proceso de préstamo.

Ejemplo:

```json
{
  "accesorios": [
    {
      "nombre": "Puntas para osciloscopio",
      "cantidad": 2
    }
  ]
}
```

---

# 7. Devoluciones

| Método  | Endpoint                            | Descripción                                                | US relacionada |
| ------- | ----------------------------------- | ---------------------------------------------------------- | -------------- |
| `POST`  | `/api/devoluciones`                 | Iniciar la devolución de un equipo prestado.               | US-06, US-12   |
| `PATCH` | `/api/devoluciones/{id}/accesorios` | Registrar los accesorios entregados y faltantes.           | US-07          |
| `PATCH` | `/api/devoluciones/{id}/falla`      | Registrar si el equipo presentó alguna falla.              | US-08          |
| `POST`  | `/api/devoluciones/{id}/cerrar`     | Finalizar la devolución y actualizar el estado del equipo. | US-08          |

### POST `/api/devoluciones`

La devolución puede iniciarse escaneando directamente el RFID del equipo.

El sistema consulta quién tiene actualmente el equipo y muestra al encargado:

* estudiante;
* equipo;
* fecha del préstamo;
* accesorios registrados.

---

# 8. Registro de fallas

Las fallas no tienen como objetivo determinar culpables.

Su propósito es mantener un historial técnico del estado de los equipos y facilitar su revisión y mantenimiento.

### PATCH `/api/devoluciones/{id}/falla`

#### Request

```json
{
  "hubo_falla": true,
  "descripcion": "Falso contacto en canal 1"
}
```

Si existe una falla:

* se registra en el historial del equipo;
* el equipo pasa a estado `En revisión`.

Si no existe una falla:

* la devolución continúa normalmente;
* el equipo puede regresar a estado `Disponible`.

---

# 9. Historial

LABTRACK conservará el historial de movimientos de estudiantes y equipos.

## Historial de estudiante

Debe permitir consultar:

* equipos actualmente prestados;
* préstamos anteriores;
* fechas de préstamo y devolución;
* accesorios registrados.

## Historial de equipo

Debe permitir consultar:

* estado actual;
* préstamos anteriores;
* devoluciones;
* fallas registradas;
* cantidad de fallas acumuladas.

El historial permitirá consultar la ficha de un equipo, por ejemplo:

```text
OSC-0307

Estado: Disponible
Fallas registradas: 2

Historial de fallas:
1. Falso contacto en canal 1
2. Canal 2 sin señal
```

---

# 10. Registro manual de respaldo

El sistema contará con un mecanismo manual para continuar operando si el lector RFID no está disponible.

| Método | Endpoint                    | Descripción                                              | US relacionada |
| ------ | --------------------------- | -------------------------------------------------------- | -------------- |
| `POST` | `/api/pedidos`              | Abrir un pedido seleccionando manualmente al estudiante. | US-12          |
| `POST` | `/api/pedidos/{id}/equipos` | Agregar manualmente un equipo.                           | US-12          |
| `POST` | `/api/devoluciones`         | Iniciar manualmente una devolución.                      | US-12          |

El flujo manual utilizará la misma lógica de negocio que el flujo mediante RFID, evitando duplicar reglas en el sistema.

---

# 11. Códigos de respuesta

La API utilizará códigos HTTP estándar.

| Código | Uso                                             |
| ------ | ----------------------------------------------- |
| `200`  | Operación realizada correctamente.              |
| `201`  | Recurso creado correctamente.                   |
| `404`  | Recurso no encontrado.                          |
| `409`  | Conflicto con el estado actual del recurso.     |
| `422`  | Datos enviados con formato o valores inválidos. |

### Ejemplos de conflictos (`409`)

* Código de equipo ya registrado.
* UID RFID ya asociado.
* Intentar prestar un equipo que ya está prestado.
* Intentar devolver un equipo que no tiene un préstamo activo.

### Ejemplos de datos inválidos (`422`)

* Cantidad negativa de accesorios.
* Datos obligatorios ausentes.
* Valores que no cumplen las validaciones definidas.

---

# 12. Flujo principal del MVP

El contrato de API está diseñado alrededor del siguiente flujo:

```text
1. Escanear credencial RFID
        ↓
2. Identificar estudiante
        ↓
3. Abrir automáticamente su pedido
        ↓
4. Escanear equipo RFID
        ↓
5. Agregar automáticamente el equipo
        ↓
6. Registrar accesorios
        ↓
7. Escanear otros equipos si es necesario
        ↓
8. Cerrar pedido
        ↓
9. Equipos → Prestado


        ... tiempo después ...


10. Escanear equipo RFID
        ↓
11. Identificar estudiante que lo tiene
        ↓
12. Mostrar datos del préstamo
        ↓
13. Confirmar accesorios
        ↓
14. Registrar falla si existe
        ↓
15. Cerrar devolución
        ↓
16. Equipo → Disponible / En revisión
```

---

# 13. Alcance del contrato

Este documento representa el **borrador del contrato de API para la Compuerta 1**.

Durante la construcción podrán definirse con mayor precisión:

* schemas de request y response;
* tipos de datos;
* validaciones;
* autenticación;
* paginación;
* filtros;
* relaciones entre recursos;
* códigos de error específicos;
* documentación OpenAPI.

Los cambios importantes al alcance deberán registrarse mediante un ADR conforme al proceso del Reto Final EDSIA 2026.

# Borrador del contrato de API — LABTRACK

> **Estado:** *Borrador — Compuerta 1*
> **Versión:** *0.2*
> **Propósito:** *Definir las operaciones principales de la API del MVP antes de su implementación.*

---

# 1. Objetivo

LABTRACK contará con una API REST para gestionar el préstamo, devolución y seguimiento de equipos de laboratorio.

La API será utilizada principalmente por la interfaz web del encargado y por el dispositivo ESP32-S3 encargado de capturar identificaciones físicas.

LABTRACK utilizará dos mecanismos de identificación:

* **RFID:** para identificar al estudiante mediante su credencial.
* **QR:** para identificar al equipo mediante el código físico colocado en el equipo.

El ESP32-S3 actúa únicamente como dispositivo de captura y comunicación. La lógica de negocio y las decisiones del sistema permanecen centralizadas en el backend.

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

El código del equipo será único. Este mismo código será utilizado como valor codificado en su código QR.

Ejemplo:

```text
Equipo:
codigo = OSC-0307

QR:
OSC-0307
```

El QR no almacenará el ID interno de la base de datos.

---

# 4. Identificación física

LABTRACK utiliza dos mecanismos de identificación física:

```text
Credencial RFID
      ↓
   ESP32-S3
      ↓
   UID RFID
      ↓
    Backend
      ↓
  Estudiante
```

y:

```text
QR del equipo
      ↓
Cámara ESP32-S3
      ↓
 Código del equipo
      ↓
    Backend
      ↓
    Equipo
```

El ESP32-S3 no contiene lógica de negocio. Su función es capturar el identificador correspondiente y enviarlo al backend mediante HTTP.

## POST `/api/identificaciones/scan`

Recibe una identificación física y permite que el backend determine cómo continuar el flujo según el contexto actual.

### Request RFID

```json
{
  "tipo": "rfid",
  "valor": "A1B2C3D4",
  "lector_id": "esp32-mesa-1"
}
```

### Request QR

```json
{
  "tipo": "qr",
  "valor": "OSC-0307",
  "lector_id": "esp32-mesa-1"
}
```

El campo `tipo` permite distinguir entre una identificación RFID y una identificación QR.

La API será responsable de resolver el identificador y ejecutar la acción correspondiente.

---

# 5. Identificación de estudiante mediante RFID

Cuando se escanea la credencial RFID de un estudiante, el backend:

1. Busca el UID RFID.
2. Si no está registrado, devuelve un error.
3. Si está registrado, consulta si existe una sesión activa.
4. Si no existe, abre una nueva sesión.
5. Si existe, continúa la sesión existente.
6. Devuelve la información necesaria para continuar el flujo.

### Ejemplo de respuesta

```json
{
  "tipo": "estudiante",
  "estudiante_id": 15,
  "nombre": "Alberto",
  "accion": "sesion_abierta",
  "sesion_id": 42,
  "equipos_actuales": []
}
```

Si ya existe una sesión:

```json
{
  "tipo": "estudiante",
  "estudiante_id": 15,
  "nombre": "Alberto",
  "accion": "sesion_continuada",
  "sesion_id": 42,
  "equipos_actuales": [
    "OSC-0307"
  ]
}
```

---

# 6. Identificación de equipo mediante QR

Cuando existe una sesión activa y se escanea el QR de un equipo, el backend:

1. Busca el código del equipo.
2. Si no existe, devuelve un error.
3. Consulta el estado actual del equipo.
4. Si está `Disponible`, permite agregarlo al préstamo.
5. Si está `Prestado`, inicia el flujo de devolución.
6. Si está `En revisión`, muestra las fallas registradas y permite al encargado decidir si el equipo puede prestarse.

### Ejemplo: equipo disponible

```json
{
  "tipo": "equipo",
  "codigo": "OSC-0307",
  "estado": "disponible",
  "accion": "agregado_a_sesion",
  "sesion_id": 42,
  "accesorios_sugeridos": [
    {
      "nombre": "Puntas para osciloscopio",
      "cantidad_default": 2
    }
  ]
}
```

### Ejemplo: equipo en revisión

```json
{
  "tipo": "equipo",
  "codigo": "OSC-0307",
  "estado": "en_revision",
  "accion": "requiere_autorizacion",
  "fallas": [
    {
      "descripcion": "Falso contacto en canal 1",
      "estado": "pendiente"
    }
  ]
}
```

El backend no decide automáticamente si se presta un equipo `En revisión`. La decisión corresponde al encargado.

---

# 7. Enrolamiento RFID

| Método | Endpoint                        | Descripción                          | US relacionada |
| ------ | ------------------------------- | ------------------------------------ | -------------- |
| `POST` | `/api/identificaciones/enrolar` | Asociar un UID RFID a un estudiante. | US-09          |

El enrolamiento permitirá asociar una nueva credencial RFID con un estudiante registrado.

### Ejemplo

```json
{
  "tipo": "rfid",
  "valor": "A1B2C3D4",
  "estudiante_id": 15
}
```

El sistema deberá impedir que un mismo UID RFID sea asociado a más de un estudiante.

---

# 8. Pedidos / sesiones de préstamo

Una sesión representa la operación de préstamo activa de un estudiante y puede contener uno o varios equipos.

El flujo está diseñado para que el encargado pueda escanear varios equipos consecutivamente sin tener que abrir un pedido nuevo por cada equipo.

| Método | Endpoint                                            | Descripción                                       | US relacionada |
| ------ | --------------------------------------------------- | ------------------------------------------------- | -------------- |
| `POST` | `/api/sesiones`                                     | Abrir manualmente una sesión para un estudiante.  | US-02, US-12   |
| `GET`  | `/api/sesiones/activas?estudiante_id={id}`          | Consultar la sesión activa de un estudiante.      | US-02          |
| `POST` | `/api/sesiones/{id}/equipos`                        | Agregar manualmente un equipo a una sesión.       | US-03, US-12   |
| `PUT`  | `/api/sesiones/{id}/equipos/{equipo_id}/accesorios` | Registrar los accesorios prestados con un equipo. | US-04          |
| `POST` | `/api/sesiones/{id}/cerrar`                         | Finalizar la entrega de los equipos de la sesión. | US-05          |

La sesión permanece activa mientras existan equipos pendientes de devolución.

Una sesión se cierra cuando todos los equipos asociados han sido devueltos.

---

# 9. Accesorios

Los accesorios se registran asociados al préstamo específico de un equipo.

Los tipos de accesorios pueden estar relacionados con un tipo de equipo para proporcionar sugerencias al encargado.

Ejemplos:

* Osciloscopio → puntas de osciloscopio.
* Generador → puntas o cables correspondientes.
* Fuente → cables de alimentación o conexión.

La cantidad será introducida o confirmada por el encargado durante el proceso de préstamo.

### Ejemplo

```json
{
  "accesorios": [
    {
      "tipo_accesorio_id": 1,
      "cantidad": 2
    }
  ]
}
```

Durante la devolución se conservará la cantidad originalmente prestada y se registrará la cantidad efectivamente devuelta.

---

# 10. Devoluciones

| Método  | Endpoint                            | Descripción                                                | US relacionada |
| ------- | ----------------------------------- | ---------------------------------------------------------- | -------------- |
| `POST`  | `/api/devoluciones`                 | Iniciar la devolución de un equipo prestado.               | US-06, US-12   |
| `PATCH` | `/api/devoluciones/{id}/accesorios` | Registrar los accesorios entregados y faltantes.           | US-07          |
| `PATCH` | `/api/devoluciones/{id}/falla`      | Registrar si el equipo presenta una falla.                 | US-08          |
| `POST`  | `/api/devoluciones/{id}/cerrar`     | Finalizar la devolución y actualizar el estado del equipo. | US-08          |

La devolución normalmente se inicia escaneando el código QR del equipo.

El sistema consulta automáticamente quién tiene actualmente el equipo y muestra al encargado:

* estudiante;
* equipo;
* fecha del préstamo;
* accesorios registrados.

### Ejemplo

```json
{
  "equipo": {
    "codigo": "OSC-0307"
  },
  "estudiante": {
    "id": 15,
    "nombre": "Alberto"
  },
  "fecha_prestamo": "2026-09-02T10:30:00",
  "accesorios": [
    {
      "nombre": "Puntas para osciloscopio",
      "cantidad_prestada": 2
    }
  ]
}
```

---

# 11. Registro de fallas

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

* se registra como un nuevo registro en el historial del equipo;
* el equipo pasa a estado `En revisión`;
* la falla queda inicialmente como `pendiente`.

Si no existe una falla:

* la devolución continúa normalmente;
* el equipo puede regresar a estado `Disponible`.

Las fallas anteriores no se sobrescriben ni eliminan.

---

# 12. Resolución de fallas

El encargado podrá marcar una falla como resuelta cuando haya sido reparada o cuando se haya verificado que el equipo funciona correctamente.

### PATCH `/api/fallas/{id}`

#### Ejemplo

```json
{
  "estado": "resuelta",
  "observacion_resolucion": "Se verificó funcionamiento correcto."
}
```

También podrá registrarse una reparación específica:

```json
{
  "estado": "resuelta",
  "observacion_resolucion": "Se reemplazó el conector del canal 1."
}
```

Al resolver una falla, el sistema conservará el registro histórico de la incidencia.

El estado general del equipo podrá regresar a `Disponible` cuando ya no existan fallas pendientes que requieran mantenerlo en revisión.

---

# 13. Historial

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
* estado de las fallas;
* cantidad de fallas acumuladas.

### Ejemplo

```text
OSC-0307

Estado: Disponible

Fallas registradas: 2

Historial de fallas:

1. Falso contacto en canal 1
   Estado: Resuelta

2. Canal 2 sin señal
   Estado: Pendiente
```

El historial conserva las incidencias anteriores aunque hayan sido resueltas.

---

# 14. Registro manual de respaldo

El sistema contará con un mecanismo manual para continuar operando si el lector RFID o el dispositivo de identificación no está disponible.

| Método | Endpoint                     | Descripción                                               | US relacionada |
| ------ | ---------------------------- | --------------------------------------------------------- | -------------- |
| `POST` | `/api/sesiones`              | Abrir manualmente una sesión seleccionando al estudiante. | US-12          |
| `POST` | `/api/sesiones/{id}/equipos` | Agregar manualmente un equipo.                            | US-12          |
| `POST` | `/api/devoluciones`          | Iniciar manualmente una devolución.                       | US-12          |

El flujo manual utilizará la misma lógica de negocio que el flujo mediante RFID y QR, evitando duplicar reglas en el sistema.

---

# 15. Códigos de respuesta

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
* Intentar registrar una segunda sesión activa para el mismo estudiante cuando no corresponde.

### Ejemplos de datos inválidos (`422`)

* Cantidad negativa de accesorios.
* Datos obligatorios ausentes.
* Valores que no cumplen las validaciones definidas.

---

# 16. Flujo principal del MVP

El contrato de API está diseñado alrededor del siguiente flujo:

```text
1. Escanear credencial RFID
           ↓
2. Identificar estudiante
           ↓
3. Abrir o continuar sesión
           ↓
4. Escanear QR del equipo
           ↓
5. Verificar estado del equipo
           ↓
6. Si está disponible → agregar al préstamo
           ↓
7. Si está en revisión → mostrar fallas y solicitar decisión
           ↓
8. Registrar accesorios
           ↓
9. Escanear otros equipos si es necesario
           ↓
10. Cerrar entrega
           ↓
11. Equipos → Prestado


        ... tiempo después ...


12. Escanear QR del equipo
           ↓
13. Identificar automáticamente al estudiante
           ↓
14. Mostrar datos del préstamo
           ↓
15. Confirmar accesorios
           ↓
16. Registrar falla si existe
           ↓
17. Cerrar devolución
           ↓
18. Equipo → Disponible / En revisión
           ↓
19. ¿Quedan equipos pendientes?
           │
        ┌──┴──┐
       SÍ     NO
        │      │
        ↓      ↓
   Continuar  Cerrar sesión
   devolución  y devolver
               credencial
```

---

# 17. Alcance del contrato

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

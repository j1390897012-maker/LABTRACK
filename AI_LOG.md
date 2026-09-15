# Registro de Decisiones de Inteligencia Artificial (AI_LOG)
**Proyecto:** LABTRACK
**Responsable:** Alexander Torres Andrade

Este documento registra las consultas clave realizadas a la IA durante el desarrollo del sistema, las alternativas propuestas y la justificación de las decisiones arquitectónicas y de código adoptadas para el MVP.

---

## US-01: Registrar un equipo (Responsable: Alberto)

**Consulta 1: Generación y escalado de códigos QR**
* **Pregunta a la IA:** Al registrar un equipo, necesito generar un código QR automáticamente para que la aplicación móvil lo pueda leer. ¿Cómo aseguro que la imagen generada tenga la resolución correcta para imprimirse sin que la cámara del celular falle al enfocar?
* **Respuesta de la IA:** Utiliza la librería `qrcode` combinada con `Pillow (PIL)`. En tu servicio, puedes definir el tamaño físico (ej. 4x4 cm) y los DPI (puntos por pulgada). Escala la imagen usando `Resampling.NEAREST` para no perder la nitidez de los bordes de los píxeles del QR y conviértelo a Base64 para enviarlo al frontend.
* **Decisión:** **Aceptado.** Implementado en `EquipoService._generar_qr_data_uri`. Esto permite que el backend devuelva directamente un URI `data:image/png;base64,...` listo para que el frontend lo muestre o imprima con las dimensiones exactas.

---

## US-02: Identificar estudiante vía NFC

**Consulta 1: Arquitectura del endpoint de escaneo**
* **Pregunta a la IA:** Necesito diseñar el endpoint para recibir las lecturas físicas. ¿Debería hacer un endpoint específico `POST /api/estudiantes/nfc` y otro `POST /api/equipos/qr`, o me conviene unificados?
* **Respuesta de la IA:** Recomiendo crear un único endpoint genérico (ej. `POST /api/identificaciones/scan`) que reciba un payload con el `tipo` ('rfid' o 'qr') y el `valor`. En tu capa de servicios, puedes usar un enrutador interno o condicionales (como `_procesar_rfid` y `_procesar_qr`) para delegar la lógica.
* **Decisión:** **Aceptado.** Mantiene el controlador (router) mucho más limpio y centraliza la entrada de todas las identificaciones, lo cual facilita la integración de las peticiones HTTP desde la Aplicación Móvil LABTRACK.

**Consulta 2: Manejo de estados de sesión**
* **Pregunta a la IA:** Cuando identifico al estudiante por NFC, ¿cómo estructuro la respuesta JSON para que la app móvil sepa si debe abrir una sesión nueva o mostrar la que ya tiene abierta?
* **Respuesta de la IA:** Puedes incluir un campo de metadatos llamado `accion` en tu esquema de respuesta (Pydantic). Si no tiene sesión activa, devuelves `accion: "sesion_abierta"`. Si ya la tiene, devuelves `accion: "sesion_continuada"` y adjuntas una lista en un campo `equipos_actuales` con los códigos de los equipos que ya tiene en su poder.
* **Decisión:** **Aceptado.** Se implementó exactamente así en el esquema `IdentificacionResponse`, lo que permite que el frontend reaccione de forma dinámica sin tener que hacer una segunda petición para consultar el estado.

**Consulta 3: Sincronización web (Polling)**
* **Pregunta a la IA:** La interfaz web estática necesita saber cuál fue el último tag escaneado (NFC/QR) para autocompletar flujos en pruebas. ¿Debo implementar WebSockets obligatoriamente en FastAPI?
* **Respuesta de la IA:** Para un MVP, WebSockets puede añadir complejidad innecesaria en la infraestructura. Una alternativa pragmática es almacenar el último escaneo en memoria dentro de tu clase `IdentificacionService` y exponer un endpoint `GET /api/identificaciones/ultimo-scan` para que el cliente web haga *Short Polling* temporalmente.
* **Decisión:** **Aceptado.** Es una solución rápida que evita configurar administradores de conexiones complejas en esta etapa temprana. Se implementó en `identificaciones.py`.

---

## US-03: Agregar equipo a una sesión vía QR (Responsable: Alberto)

**Consulta 1: Reutilización de lógica de negocio**
* **Pregunta a la IA:** Cuando se escanea un QR con la app para agregarlo a una sesión, ¿debo hacer toda la lógica de validación de disponibilidad y registro dentro de la respuesta del escáner?
* **Respuesta de la IA:** No, mantén la separación de responsabilidades. El endpoint del escáner (`/api/identificaciones/scan`) solo debe validar que el equipo esté "Disponible" y devolver un comando de acción (`accion="confirmar_prestamo"`). El frontend usará esa respuesta para llamar al endpoint dedicado `POST /api/equipos/prestar`, reutilizando así el mismo flujo.
* **Decisión:** **Aceptado.** Esta delegación se implementó en `IdentificacionService._procesar_qr`, manteniendo el servicio de identificaciones ligero y concentrando las transacciones de base de datos en `PrestamoService`.

---

## US-04: Registrar accesorios del préstamo

**Consulta 1: Validación de cantidades de accesorios**
* **Pregunta a la IA:** Quiero asegurarme de que al momento de registrar accesorios en un préstamo, la cantidad ingresada por el encargado nunca sea 0 o negativa. ¿Cuál es la mejor forma de validarlo en FastAPI antes de que llegue al servicio?
* **Respuesta de la IA:** La forma más robusta es utilizar la función `Field` de Pydantic en tus esquemas. En tu modelo `AccesorioPrestamoCreate`, define el campo así: `cantidad: int = Field(gt=0)`. FastAPI interceptará automáticamente cualquier valor menor o igual a cero y devolverá un error HTTP 422 (Unprocessable Entity).
* **Decisión:** **Aceptado.** Se integró en la capa de esquemas (`app/schemas/prestamo.py`). Esto actúa como un escudo protector y evita ensuciar el `PrestamoService` con condicionales `if cantidad <= 0`.

---

## US-05: Cerrar entrega de préstamo (Responsable: Alberto)

**Consulta 1: Prevención de sesiones fantasma**
* **Pregunta a la IA:** ¿Qué pasa si el encargado abre la sesión de un estudiante escaneando su NFC, pero por algún motivo no escanea ningún equipo y le da al botón de cerrar entrega?
* **Respuesta de la IA:** Debes prevenir que se guarden "sesiones vacías". En `SesionService.cerrar_entrega`, implementa una regla que busque cuántos equipos están vinculados a `sesion_id`. Si la lista está vacía, lanza una excepción `HTTP 400 Bad Request`.
* **Decisión:** **Aceptado.** Se agregó esta validación exacta antes de ejecutar `repo_sesion.cerrar_sesion(db, sesion)`. Esto mantiene la limpieza en la base de datos y evita historiales de préstamo sin sentido.

---

## US-06: Iniciar devolución vía QR (Responsable: Alejandro)

**Consulta 1: Búsqueda del préstamo activo**
* **Pregunta a la IA:** Un equipo como un osciloscopio tendrá decenas de préstamos en su historial. Cuando escaneo su QR para devolverlo, ¿cómo me aseguro de jalar los datos del estudiante que lo tiene *ahorita* y no los de un préstamo de ayer?
* **Respuesta de la IA:** Crea un método específico en tu repositorio (ej. `get_prestamo_activo_by_equipo`) que filtre cruzando dos condiciones: el `equipo_id` y que el estado en la tabla pivot `sesion_equipos` sea estrictamente `"Prestado"`. Usar `scalar_one_or_none()` garantizará que solo traigas el registro en curso.
* **Decisión:** **Aceptado.** Implementado en `SesionRepository`. Se usa tanto en el escaneo automático (`IdentificacionService`) como en el inicio de devolución manual (`DevolucionService.iniciar_devolucion_manual`).

---

## US-07: Confirmar accesorios devueltos (Responsable: Alejandro)

**Consulta 1: Validación de entregas parciales**
* **Pregunta a la IA:** Al confirmar la devolución, el encargado ingresa cuántas puntas de osciloscopio regresó el estudiante. ¿Cómo prevengo que por error teclee que devolvió 3 puntas si solo se le prestaron 2?
* **Respuesta de la IA:** En tu iteración dentro de `DevolucionService.confirmar_devolucion`, antes de hacer el update en base de datos, extrae el registro de `cantidad_prestada` original. Agrega un bloque condicional: si `cantidad_devuelta > cantidad_prestada`, aborta la transacción con un `HTTP 400`.
* **Decisión:** **Aceptado.** Esta validación quedó firme en la capa de servicios, protegiendo la integridad del inventario de accesorios directamente en el backend.

---

## US-08: Registrar falla al devolver un equipo (Responsable: Alejandro)

**Consulta 1: Trazabilidad de las incidencias**
* **Pregunta a la IA:** Si un equipo se devuelve con falla, ¿el sistema debe borrar esa falla cuando se repare para que no estorbe?
* **Respuesta de la IA:** Técnicamente puedes borrarla, pero para un sistema de laboratorio **nunca debes borrar incidencias**. Crea una tabla independiente de `fallas`. Cuando se registre un problema, inserta un nuevo registro en estado "Pendiente" y cambia el equipo a "En revisión". Cuando se repare, marca esa falla como "Resuelta". Esto genera un bitácora histórica invaluable para mantenimiento.
* **Decisión:** **Aceptado.** El flujo completo se diseñó así en `DevolucionService.registrar_falla` y `FallaService.resolver`, manteniendo intacto el registro (US-10) de problemas pasados.

---

## US-09: Enrolar una tarjeta RFID/NFC de estudiante (Responsable: Alejandro)

**Consulta 1: Choques de identificadores físicos**
* **Pregunta a la IA:** ¿Cómo evito que la misma tarjeta NFC sea enrolada por accidente a dos estudiantes diferentes en la base de datos?
* **Respuesta de la IA:** A nivel de esquema de base de datos (`models.py`), añade `unique=True` a la columna `uid_rfid`. A nivel de servicio, antes de hacer el UPDATE, ejecuta un `GET` buscando ese UID. Si existe y el ID del estudiante no coincide con el que estás actualizando, lanza un error `409 Conflict`.
* **Decisión:** **Aceptado.** Se añadieron ambas capas de protección (en `app/models/labtrack.py` y en `IdentificacionService.enrolar_rfid`), garantizando correspondencia uno a uno entre credencial y alumno.

---

## US-10: Consultar historial de un equipo

**Consulta 1: Carga eficiente de relaciones (Problema N+1)**
* **Pregunta a la IA:** Para el historial de un equipo, necesito devolver la información del préstamo, el estudiante, los accesorios y las fallas en una sola petición. Si hago un simple `select()`, SQLAlchemy hace decenas de consultas individuales a la base de datos cuando intento acceder a cada relación (el problema N+1). ¿Cuál es la forma óptima de resolverlo en SQLAlchemy 2.0?
* **Respuesta de la IA:** Para cargar colecciones anidadas de forma eficiente, debes utilizar la función `selectinload()` dentro de `.options()` en tu consulta. A diferencia de `joinedload()` (que hace JOINs masivos y puede multiplicar filas), `selectinload` emite una sola consulta adicional por cada relación usando cláusulas `IN (...)`. Quedaría estructurado encadenando las relaciones: `.options(selectinload(SesionEquipo.sesion).selectinload(Sesion.estudiante))`.
* **Decisión:** **Aceptado.** Se implementó en `SesionRepository.get_historial_by_equipo`. Esto redujo drásticamente el tiempo de respuesta del endpoint `/api/equipos/{codigo}/historial`, extrayendo todo el árbol de relaciones con unas pocas consultas SQL limpias y predecibles.

---

## US-11: Consultar historial de un estudiante

**Consulta 1: Ordenamiento de colecciones anidadas**
* **Pregunta a la IA:** Al traer el historial completo de un estudiante usando `selectinload`, necesito que las sesiones vengan ordenadas para que las más recientes aparezcan primero. Intenté usar `order_by()` en la consulta base, pero no aplica al orden interno de la lista de sesiones mapeada. ¿Cómo filtro u ordeno esto?
* **Respuesta de la IA:** Ordenar relaciones cargadas con `selectinload` directamente en la consulta SQL es complejo porque SQLAlchemy las resuelve en peticiones separadas. Dado que el volumen de sesiones históricas por estudiante en un cuatrimestre es manejable en memoria, la solución más pragmática y limpia es traer el objeto completo y realizar el ordenamiento en Python a nivel del servicio utilizando `sorted(estudiante.sesiones, key=lambda s: s.fecha_apertura, reverse=True)`.
* **Decisión:** **Aceptado.** Se aplicó este enfoque en `EstudianteService.obtener_historial`. Esto mantuvo el repositorio (`EstudianteRepository.get_historial_completo`) enfocado puramente en la extracción de datos, delegando la regla de visualización (orden descendente) a la capa de servicios.

---

## US-12: Registro manual de respaldo (Responsable: Equipo)

**Consulta 1: Integración con el flujo existente**
* **Pregunta a la IA:** Si la cámara del celular falla y el encargado tiene que meter la matrícula y el código manualmente en un formulario, ¿tengo que reescribir toda la lógica de préstamo para este endpoint manual?
* **Respuesta de la IA:** No. Tu endpoint manual debe servir únicamente como un puente. Recibe los identificadores en texto, resuelve cuáles son sus IDs internos en la base de datos, y luego inyecta esa información llamando exactamente a las mismas funciones del servicio (ej. `PrestamoService.confirmar_prestamo`).
* **Decisión:** **Aceptado.** Se implementó así en `SesionService.prestamo_manual`. Esto evita duplicar código y asegura que un préstamo manual pase por las mismas validaciones de estado y accesorios que un préstamo por NFC/QR.

---

## US-13: Registrar un estudiante

**Consulta 1: Filtros de búsqueda insensibles a mayúsculas**
* **Pregunta a la IA:** En la pantalla de registro, necesito un endpoint que permita buscar si el estudiante ya existe. ¿Cómo estructuro el filtro en SQLAlchemy para que la búsqueda por nombre o matrícula ignore mayúsculas/minúsculas y permita coincidencias parciales (por ejemplo, buscar "alberto" y que me devuelva "Luis Alberto")?
* **Respuesta de la IA:** Debes utilizar el operador `ilike()` nativo de SQLAlchemy, el cual genera consultas `ILIKE` en PostgreSQL (búsqueda insensible a mayúsculas). Para permitir coincidencias parciales, debes concatenar el comodín `%` de SQL a tu variable. La sentencia quedaría así: `stmt.where(Estudiante.nombre.ilike(f"%{nombre}%"))`.
* **Decisión:** **Aceptado.** Implementado en el método `search` de `EstudianteRepository`. Esta solución dotó al endpoint `GET /api/estudiantes` de la flexibilidad necesaria para que el frontend pueda construir un buscador dinámico sin requerir coincidencias exactas.
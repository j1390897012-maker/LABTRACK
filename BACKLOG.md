
---

# Product Backlog – LABTRACK

## Descripción del producto

Sistema para digitalizar el préstamo, devolución y seguimiento de equipo de laboratorio, con identificación física mediante RFID.

---

# User Stories

## US-01: Registrar un equipo

**Story Points:** 3

**Como** encargado del laboratorio,

**quiero** registrar un nuevo equipo con su código y tipo,

**para** poder prestarlo dentro del sistema.

**Escenario:** Registrar un equipo correctamente

**Given** el sistema está disponible para registrar equipos,

**When** el encargado agrega un equipo con código "OSC-0307" y tipo "Osciloscopio",

**Then** el sistema muestra el mensaje "Equipo registrado",

**And** el equipo aparece en la lista con estado "Disponible".

---

**Escenario:** Registrar un equipo con código repetido

**Given** existe un equipo registrado con código "OSC-0307",

**When** el encargado intenta registrar otro equipo con el mismo código,

**Then** el sistema muestra un mensaje de error indicando que el código ya existe.

## US-02: Identificar estudiante vía RFID

**Story Points:** 5

**Como** encargado del laboratorio,

**quiero** identificar a un estudiante acercando su tarjeta RFID,

**para** abrir un pedido de préstamo a su nombre sin escribir datos manualmente.

**Escenario:** Identificar a un estudiante registrado

**Given** un estudiante "Alberto" tiene una tarjeta RFID asociada en el sistema,

**When** el ESP32 lee su tarjeta y envía el UID a la API,

**Then** el sistema abre un pedido activo a nombre de Alberto,

**And** muestra sus equipos actuales en préstamo.

---

**Escenario:** Leer una tarjeta no registrada

**Given** una tarjeta RFID cuyo UID no está asociado a ningún estudiante,

**When** el ESP32 envía ese UID a la API,

**Then** el sistema informa que la tarjeta no está registrada,

**And** no abre ningún pedido.

## US-03: Agregar equipo a un pedido vía RFID

**Story Points:** 5

**Como** encargado del laboratorio,

**quiero** escanear el tag RFID de un equipo,

**para** agregarlo automáticamente al pedido abierto del estudiante.

**Escenario:** Agregar un equipo disponible al pedido

**Given** existe un pedido abierto para "Alberto" y un equipo "OSC-0307" con estado "Disponible",

**When** el ESP32 lee el tag de "OSC-0307",

**Then** el sistema agrega el equipo al pedido de Alberto,

**And** muestra los accesorios correspondientes al tipo de equipo.

---

**Escenario:** Escanear un equipo que ya está prestado

**Given** el equipo "OSC-0307" tiene estado "Prestado",

**When** el encargado intenta agregarlo a un nuevo pedido,

**Then** el sistema muestra un mensaje de error indicando que el equipo no está disponible.

## US-04: Registrar accesorios del pedido

**Story Points:** 3

**Como** encargado del laboratorio,

**quiero** indicar cuántos accesorios se lleva el estudiante al agregar un equipo,

**para** tener un registro exacto de lo prestado.

**Escenario:** Registrar accesorios correctamente

**Given** un equipo "OSC-0307" fue agregado al pedido de Alberto,

**When** el encargado indica que se lleva 2 puntas de osciloscopio,

**Then** el sistema guarda esa cantidad asociada al préstamo.

---

**Escenario:** Registrar una cantidad de accesorios inválida

**Given** un equipo fue agregado al pedido,

**When** el encargado introduce una cantidad negativa de accesorios,

**Then** el sistema muestra un mensaje indicando que el valor no es válido.

## US-05: Cerrar un pedido de préstamo

**Story Points:** 3

**Como** encargado del laboratorio,

**quiero** cerrar el pedido activo de un estudiante,

**para** que los equipos queden marcados como prestados.

**Escenario:** Cerrar un pedido con equipos

**Given** un pedido abierto de Alberto contiene al menos un equipo,

**When** el encargado cierra el pedido,

**Then** el sistema marca los equipos incluidos como "Prestado",

**And** el pedido deja de estar activo.

---

**Escenario:** Cerrar un pedido vacío

**Given** un pedido abierto de Alberto no tiene ningún equipo agregado,

**When** el encargado intenta cerrarlo,

**Then** el sistema muestra un mensaje indicando que el pedido está vacío.

## US-06: Iniciar devolución vía RFID

**Story Points:** 5

**Como** encargado del laboratorio,

**quiero** escanear el tag de un equipo para iniciar su devolución,

**para** que el sistema identifique automáticamente quién lo tiene.

**Escenario:** Iniciar devolución de un equipo prestado

**Given** el equipo "OSC-0307" está prestado a Alberto,

**When** el ESP32 lee el tag del equipo,

**Then** el sistema muestra la pantalla de devolución con los datos de Alberto y los accesorios que se llevó.

---

**Escenario:** Escanear un equipo que no está prestado

**Given** el equipo "OSC-0307" tiene estado "Disponible",

**When** el encargado intenta iniciar una devolución con ese equipo,

**Then** el sistema informa que el equipo no tiene un préstamo activo.

## US-07: Confirmar entrega de accesorios en devolución

**Story Points:** 3

**Como** encargado del laboratorio,

**quiero** confirmar si el estudiante entregó todos los accesorios,

**para** dejar constancia de una devolución completa o incompleta.

**Escenario:** Confirmar entrega completa

**Given** una devolución en curso del equipo "OSC-0307" con 2 puntas registradas,

**When** el encargado confirma que se entregaron las 2 puntas,

**Then** el sistema marca la devolución de accesorios como completa.

---

**Escenario:** Reportar accesorios faltantes

**Given** una devolución en curso con 2 puntas registradas,

**When** el encargado indica que solo se entregó 1,

**Then** el sistema registra el faltante en el historial de la devolución.

## US-08: Registrar falla al devolver un equipo

**Story Points:** 3

**Como** encargado del laboratorio,

**quiero** registrar una falla al momento de la devolución,

**para** dejar el equipo marcado como "En revisión".

**Escenario:** Registrar una falla

**Given** una devolución en curso del equipo "OSC-0307",

**When** el encargado indica que hubo un problema y describe "Falso contacto en canal 1",

**Then** el sistema guarda la falla en el historial del equipo,

**And** cambia su estado a "En revisión".

---

**Escenario:** Devolución sin fallas

**Given** una devolución en curso del equipo "OSC-0307",

**When** el encargado indica que no hubo ningún problema,

**Then** el sistema marca el equipo con estado "Disponible".

## US-09: Enrolar una tarjeta RFID nueva

**Story Points:** 3

**Como** encargado del laboratorio,

**quiero** asociar una tarjeta RFID nueva a un estudiante o equipo,

**para** poder identificarlos en escaneos futuros.

**Escenario:** Enrolar tarjeta correctamente

**Given** el sistema recibe un UID que no está asociado a nadie,

**When** el encargado lo asocia al estudiante "Alberto",

**Then** el sistema guarda la asociación,

**And** futuras lecturas de esa tarjeta identifican a Alberto.

---

**Escenario:** Enrolar una tarjeta ya asociada

**Given** un UID ya está asociado al estudiante "Alex",

**When** el encargado intenta asociarlo también a "Alberto",

**Then** el sistema muestra un mensaje de error indicando que la tarjeta ya está en uso.

## US-10: Consultar historial de un equipo

**Story Points:** 2

**Como** encargado del laboratorio,

**quiero** consultar la ficha e historial de un equipo,

**para** conocer su estado y fallas registradas.

**Escenario:** Consultar historial de un equipo con movimientos

**Given** el equipo "OSC-0307" tiene préstamos y fallas registradas,

**When** el encargado consulta su ficha,

**Then** el sistema muestra su estado actual y el historial ordenado por fecha.

---

**Escenario:** Consultar un equipo inexistente

**Given** no existe ningún equipo con código "OSC-9999",

**When** el encargado intenta consultarlo,

**Then** el sistema informa que el equipo no fue encontrado.

## US-11: Consultar historial de un estudiante

**Story Points:** 2

**Como** encargado del laboratorio,

**quiero** consultar el historial de préstamos de un estudiante,

**para** ver qué equipos tiene actualmente y cuáles ha pedido antes.

**Escenario:** Consultar historial de un estudiante registrado

**Given** el estudiante "Alberto" tiene préstamos previos y actuales,

**When** el encargado consulta su historial,

**Then** el sistema muestra los equipos que tiene actualmente y el historial completo.

---

**Escenario:** Consultar un estudiante sin historial

**Given** el estudiante "Alex" no tiene ningún préstamo registrado,

**When** el encargado consulta su historial,

**Then** el sistema muestra que no hay movimientos registrados.

## US-12: Registro manual de respaldo (sin RFID)

**Story Points:** 5

**Como** encargado del laboratorio,

**quiero** registrar un préstamo o devolución manualmente desde la web,

**para** seguir operando si el lector RFID falla.

**Escenario:** Registrar préstamo manual

**Given** el lector RFID no está disponible,

**When** el encargado selecciona manualmente al estudiante y el equipo desde la web,

**Then** el sistema procesa el préstamo igual que si hubiera sido leído por RFID.

---

**Escenario:** Intentar registro manual con datos incompletos

**Given** el encargado no selecciona ningún equipo,

**When** intenta confirmar el préstamo manual,

**Then** el sistema muestra un mensaje indicando que falta seleccionar un equipo.

---


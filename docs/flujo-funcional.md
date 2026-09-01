# Flujo funcional definitivo — LABTRACK

## 1. Inicio del préstamo

```text
ESTUDIANTE LLEGA
        │
        ▼
Escanear RFID de la credencial
        │
        ▼
¿Estudiante registrado?
        │
   ┌────┴────┐
  NO         SÍ
   │          │
   ▼          ▼
 Error   ¿Ya tiene sesión activa?
              │
        ┌─────┴─────┐
       NO           SÍ
        │            │
        ▼            ▼
   Abrir sesión   Continuar sesión
   (credencial    existente
    retenida)          │
        │              │
        └──────┬───────┘
               ▼
        Escanear QR del equipo
          (cámara ESP32-S3)
               │
               ▼
        ¿Equipo está registrado?
               │
          ┌────┴────┐
         NO         SÍ
          │          │
          ▼          ▼
        Error    Consultar estado
```

## 2. Decisión según el estado del equipo

```text
              Consultar estado
                     │
          ┌──────────┼──────────┐
          │          │          │
          ▼          ▼          ▼
     Disponible   Prestado   En revisión
          │          │          │
          ▼          ▼          ▼
      Continuar   Iniciar      Mostrar
      préstamo    devolución   fallas registradas
                                  │
                                  ▼
                            ¿Prestarlo?
                             │       │
                            NO      SÍ
                             │       │
                             ▼       ▼
                            Fin   Continuar
                                  préstamo
```

### Regla importante

**"En revisión" NO significa que el equipo esté bloqueado.**

Un equipo en revisión puede prestarse.

Antes de prestarlo, LABTRACK muestra las fallas conocidas para que el encargado pueda comunicárselas al estudiante.

Ejemplo:

```text
OSC-0307
Estado: EN REVISIÓN

Fallas registradas:
• Canal 2 presenta falso contacto.
• Perilla de VOLTS/DIV presenta desgaste.

[ PRESTAR ]    [ NO PRESTAR ]
```

La decisión final la toma el encargado.

---

## 3. Registrar equipo y accesorios

```text
Registrar equipo en la sesión
             │
             ▼
     Mostrar accesorios
             │
             ▼
   ¿Cuántos accesorios lleva?
             │
             ▼
     Registrar cantidades
             │
             ▼
     ¿Otro equipo?
        │          │
       SÍ         NO
        │          │
        ▼          ▼
   Escanear QR   Cerrar sesión
    nuevamente      │
                    ▼
             Equipo(s) quedan
             asociados al pedido
                    │
                    ▼
             Credencial retenida
```

El flujo de préstamo busca comportarse como un escaneo rápido: el encargado escanea equipo, registra accesorios y continúa con el siguiente.

---

# 4. Continuación de una sesión activa

Si el estudiante todavía tiene su credencial retenida y regresa por otro equipo:

```text
Estudiante regresa
       │
       ▼
Escanear RFID
       │
       ▼
Sesión existente
       │
       ▼
Continuar sesión
       │
       ▼
Escanear QR del nuevo equipo
```

No se crea otra sesión.

Todos los equipos quedan asociados al mismo pedido/sesión del estudiante.

---

# 5. Devolución

La devolución comienza al escanear el QR de un equipo que actualmente está prestado.

```text
Escanear QR del equipo
        │
        ▼
     Equipo:
      PRESTADO
        │
        ▼
Identificar automáticamente
al estudiante que lo tiene
        │
        ▼
Mostrar información de devolución
        │
        ▼
Mostrar accesorios esperados
        │
        ▼
¿Entregó todos los accesorios?
        │
    ┌───┴───┐
   SÍ       NO
    │        │
    ▼        ▼
Registrar   Registrar
entrega     faltantes
    │        │
    └───┬────┘
        ▼
¿El equipo presenta alguna falla?
        │
    ┌───┴───┐
   NO       SÍ
    │        │
    ▼        ▼
Continuar   Describir falla
             │
             ▼
        Guardar incidencia
             │
             ▼
        Equipo → EN REVISIÓN
             │
             └──────┐
                    ▼
             Registrar devolución
```

---

# 6. Después de devolver un equipo

Una vez registrada la devolución:

```text
Registrar devolución
        │
        ▼
¿Quedan equipos pendientes
en la sesión del estudiante?
        │
    ┌───┴───┐
   SÍ       NO
    │        │
    ▼        ▼
Volver a   Cerrar sesión
"Escanear    │
QR"          ▼
             Devolver
             credencial
```

Si todavía tiene equipos pendientes, **la sesión permanece abierta**.

---

# 7. Estado final del equipo

### Sin falla

```text
PRESTADO
   │
   │ devolución
   ▼
DISPONIBLE
```

### Con falla

```text
PRESTADO
   │
   │ devolución + falla
   ▼
EN REVISIÓN
```

Un equipo `EN REVISIÓN`:

* conserva su historial de fallas;
* muestra las fallas conocidas al escanearlo;
* **puede ser prestado si el encargado lo decide**;
* al ser prestado, pasa a `PRESTADO`;
* al volver a devolverse, puede regresar a `DISPONIBLE` o permanecer `EN REVISIÓN` dependiendo de si se registra una falla en esa devolución.

---

# 8. Caso excepcional: varios estudiantes con sesiones activas

Si existen varias sesiones abiertas y se escanea un equipo sin que previamente se haya identificado al estudiante:

```text
Escanear QR del equipo
        │
        ▼
Equipo disponible
        │
        ▼
¿Hay varias sesiones activas?
        │
    ┌───┴───┐
   NO       SÍ
    │        │
    ▼        ▼
Asignar    Mostrar sesiones
a la sesión activas
correspondiente       │
                      ▼
                Encargado selecciona
                estudiante
```

Este es un **caso de excepción**.

El flujo normal siempre será:

```text
RFID estudiante
      ↓
Sesión
      ↓
QR equipo
```

---

# 9. Principio general del sistema

El ESP32-S3 solamente captura identificaciones:

```text
RFID
  ↓
ESP32-S3 + RC522
  ↓
Backend

QR
  ↓
ESP32-S3 + cámara
  ↓
Backend
```

El ESP32 **no contiene la lógica del negocio**.

El backend determina:

* qué estudiante es;
* qué sesión está activa;
* qué equipo es;
* qué estado tiene;
* si corresponde préstamo o devolución;
* qué accesorios se esperan;
* qué accesorios faltan;
* qué fallas existen;
* qué debe registrarse en el historial.

**FastAPI + PostgreSQL son la fuente de verdad de LABTRACK.**

# ADR-0001: Arquitectura preliminar de LABTRACK

## Estado: Propuesto (para Compuerta 1)
## Fecha: 30 de agosto de 2026
## Equipo: 
### Alberto Hernández Landa
### José Alejandro Hernández Moralez
### Alexander Torres Andrade

## Contexto

El laboratorio de Instrumentación Electrónica registra actualmente los préstamos
de equipo en papel: el estudiante entrega su credencial, se anota manualmente
el equipo y sus accesorios, y al devolver se verifica y se tacha en el mismo
papel. Esto impide consultar quién tiene qué equipo en un momento dado, el
historial de préstamos por estudiante o por equipo, y las fallas que ha
presentado cada pieza.

LABTRACK digitaliza este flujo: préstamo, devolución, accesorios,
fallas/incidencias e historial, manteniendo el mismo proceso físico que ya
usa el laboratorio (credencial → equipo → accesorios → devolución).

El Reto Final exige un backend en Python/FastAPI/PostgreSQL/SQLAlchemy/Alembic
con API documentada (OpenAPI), y ofrece un sello de innovación (+5 pts) para
propuestas que integren hardware real, entre otras rutas. El equipo ya cuenta
con un ESP32 S3.

## Decisión

### 1. Arquitectura general

Aplicación en capas siguiendo el estándar del curso:

- Backend (FastAPI + SQLAlchemy + Alembic + PostgreSQL): expone la API REST
  documentada (OpenAPI), contiene la lógica de negocio (pedidos abiertos,
  préstamos, devoluciones, accesorios, fallas) y es la única fuente de
  verdad. Corre en Docker, con CI en GitHub Actions (ruff, mypy, pytest
  ≥80% cobertura) y despliegue continuo a producción.
- Frontend web: interfaz para el encargado del laboratorio — pantalla de
  pedido activo, escaneo, confirmación de accesorios y devoluciones.
  Consume la API vía HTTP.
- Capa de hardware (ESP32 S3 + módulo RFID RC522): dispositivo físico que lee
  el UID de las tarjetas RFID (credenciales de estudiantes y tags de
  equipos) y lo envía por HTTP a un endpoint dedicado de la API
  (POST /api/rfid/scan). No contiene lógica de negocio: solo transmite el
  UID leído.

### 2. Identificación física: RFID como sello de innovación

En vez de depender únicamente de escaneo de código QR por cámara, se usará
un lector RFID físico (ESP32 S3 + RC522) tanto para las credenciales de
estudiantes como para los tags de equipo. Esta es la pieza de hardware real
con la que el equipo busca el sello de innovación de la convocatoria.

Flujo:
1. El ESP32 lee el UID de una tarjeta RFID (credencial o equipo).
2. Envía el UID por HTTP al backend (POST /api/rfid/scan).
3. El backend resuelve el UID contra la tabla de estudiantes/equipos y
   continúa el flujo normal de pedido ya definido (abrir pedido, agregar
   equipo, preguntar accesorios, etc.).
4. El enrolamiento inicial (asociar un UID nuevo a un estudiante o equipo)
   se hace desde una pantalla simple de administración.

### 3. Alcance de esta decisión

Esta ADR cubre la arquitectura preliminar y la decisión de incluir hardware
RFID. No cubre aún el modelo de datos detallado ni el contrato de API
completo, que se documentarán por separado antes de la Compuerta 1.

## Alternativas consideradas

- Solo escaneo QR por cámara (sin hardware físico): cumple el MVP pero no
  aporta al sello de innovación; además es menos fiel al proceso físico
  real del laboratorio.


## Consecuencias

Positivas:
- Aporta una pieza de hardware real, demostrable en producción y en el
  video de entrega.
- No añade complejidad de negocio: el ESP32 S3 es un cliente más de la API,
  la lógica sigue centralizada en el backend.
- Reutiliza hardware que el equipo ya posee (ESP32 S3).

Riesgos / a vigilar:
- Requiere comprar módulos RC522 y tarjetas RFID (bajo costo, fácil de
  conseguir).
- Depende de conectividad WiFi estable del ESP32 S3 durante la demo y la
  semana de evaluación.
- Se debe definir un mecanismo de respaldo (registro manual desde la web)
  por si el lector físico falla durante la evaluación, para no perder
  puntos de "Software funcional" por falta de diagnóstico.

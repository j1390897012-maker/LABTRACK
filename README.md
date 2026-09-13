# LABTRACK - Backend

Sistema de control, trazabilidad y gestión operativa de equipos y accesorios para laboratorios de ingeniería.

## Arquitectura y Tecnologías
El proyecto está estructurado bajo los principios de **Clean Architecture** para garantizar alta cohesión y testabilidad:
- **Framework:** FastAPI
- **Base de Datos / ORM:** SQLite / PostgreSQL con SQLAlchemy y optimización de consultas (`selectinload`)
- **Validación:** Pydantic V2 (`ConfigDict`)
- **Calidad de Código:** Pytest (>97% de cobertura), Ruff y Mypy

## Endpoints Principales
- **Identificaciones:** Gestión de escaneo de tarjetas RFID y códigos QR (`/api/identificaciones/scan`).
- **Sesiones y Préstamos:** Apertura de sesiones automáticas o manuales de estudiante (`/api/sesiones`).
- **Equipos:** Registro de dispositivos y consulta de historial por código QR (`/api/equipos/codigo/{codigo}/historial`).
- **Devoluciones y Fallas:** Procesamiento de retornos y registro de incidencias técnicas (`/api/devoluciones`).

## Instalación y Ejecución Local
1. Clonar el repositorio y activar el entorno virtual:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate
   pip install -r requirements.txt
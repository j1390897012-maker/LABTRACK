# AI Development Log - LABTRACK

Este documento registra el proceso de colaboración técnica y desarrollo asistido para el backend de LABTRACK.

## Resumen de Módulos y Funcionalidades Desarrolladas
- **US-04 (Validación de accesorios):** Implementación de esquemas con Pydantic V2 y reglas de validación en la adición de componentes.
- **US-08 (Registro de fallas):** Incorporación del flujo de devolución con reporte de incidencias y actualización automática de estados del equipo ("En revisión" / "Disponible").
- **US-11 (Historial de estudiante):** Creación del endpoint de auditoría por estudiante (`GET /api/estudiantes/{id}/historial`), optimizando consultas con `selectinload` de SQLAlchemy para evitar problemas N+1 y anidando sesiones, equipos, accesorios y fallas.
- **US-10 (Historial de equipo):** Desarrollo de la consulta de trazabilidad mediante el código QR físico (`GET /api/equipos/codigo/{codigo}/historial`), conectando el escaneo directo con el historial de usos y estudiantes.
- **US-12 (Registro manual - Respaldo):** Implementación de flujos de respaldo manual para apertura de sesiones, préstamos y devoluciones ante fallas de lectura RFID o QR.

## Estándares de Calidad y Calidad de Código
- **Clean Architecture:** Separación rigurosa de responsabilidades (*Router → Service → Repository → DB*).
- **Pruebas y Cobertura:** Suite robusta de pruebas automatizadas con `pytest` alcanzando una cobertura superior al **97%**.
- **Linters y Tipado:** Verificación continua de estilo con `ruff` y tipado estricto validado mediante `mypy`.

## Bitácora de Interacciones y Soluciones por User Story
### US-11: Historial de Estudiante y Optimización de Consultas

**Contexto del reto:** Se requería implementar un endpoint para consultar el historial completo de un estudiante (sesiones pasadas, equipos prestados, accesorios y fallas asociadas) evitando problemas de consultas N+1 en SQLAlchemy.

**Prompt del usuario:**
> "Necesito implementar la US-11 para consultar el historial del estudiante, pero me preocupa que al hacer tantas relaciones anidadas (sesión -> equipos -> accesorios y fallas) se caiga en un problema de N+1 queries. ¿Cómo estructuro el repositorio con SQLAlchemy para que traiga todo de golpe de forma eficiente?"

**Respuesta del modelo:**
> La mejor forma de evitar el problema N+1 en SQLAlchemy al cargar relaciones anidadas profundas es utilizando `selectinload` de forma encadenada en el query del repositorio. Esto ejecuta consultas optimizadas en lotes en lugar de consultar la base de datos por cada elemento hijo. Aquí tienes la estructura recomendada para `EstudianteRepository`:

```Python
def get_historial_completo(self, db: Session, estudiante_id: int) -> Estudiante | None:
    stmt = (
        select(Estudiante)
        .where(Estudiante.id == estudiante_id)
        .options(
            selectinload(Estudiante.sesiones)
            .selectinload(Sesion.sesion_equipos)
            .selectinload(SesionEquipo.equipo),
            selectinload(Estudiante.sesiones)
            .selectinload(Sesion.sesion_equipos)
            .selectinload(SesionEquipo.accesorios),
            selectinload(Estudiante.sesiones)
            .selectinload(Sesion.sesion_equipos)
            .selectinload(SesionEquipo.fallas),
        )
    )
    return db.execute(stmt).scalar_one_or_none()
```

### US-10: Historial de Equipo por Código QR (Físico)

**Contexto del reto:** Inicialmente el historial de equipos dependía del ID numérico autoincremental de la base de datos, pero en el laboratorio los encargados escanean códigos físicos (ej. `OSC-0307`).

**Prompt del usuario:**
> "Alejandro revisó la US-10 y me señaló que el historial solo recibe el `equipo_id` interno, pero en el laboratorio se identifica el equipo con el código QR físico. Necesito que acepte el código (como 'OSC-0307'), busque el ID y devuelva el historial sin duplicar código ni repositorios."

**Respuesta del modelo:**
> *Podemos resolverlo agregando un método de consulta en el servicio que actúe como un puente o adaptador, reutilizando tanto el método de búsqueda por código existente en el repositorio como la lógica de historial que ya tienes probada:*

```python
def obtener_historial_por_codigo(self, db: Session, codigo: str) -> HistorialEquipoResponse:
    equipo = self.repo.get_by_codigo(db, codigo)
    if not equipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipo no encontrado.",
        )
    return self.obtener_historial(db, equipo.id)
```
Y ajustamos el router para exponerlo en `/api/equipos/codigo/{codigo}/historial.`

### US-08: Registro de Fallas y Actualización de Estados

**Contexto del reto:** Al devolver un equipo, el sistema debe registrar si hubo una falla. Si la hay, la descripción se vuelve obligatoria, el equipo pasa a estado "En revisión" y la falla se almacena permanentemente sin sobreescribir las anteriores.

**Prompt del usuario:**
> "¿Cómo valido con Pydantic V2 en el schema de registro de fallas que si `hubo_falla` es True, la descripción no venga vacía o nula, y que arroje un error claro?"

**Respuesta del modelo:**
> *En Pydantic V2, la forma idiomática y limpia de validar dependencias cruzadas entre campos de un modelo es utilizando un `@model_validator(mode="after")`. De esta forma puedes inspeccionar el estado del objeto completo:*

```python
from pydantic import BaseModel, Field, model_validator


class RegistrarFallaRequest(BaseModel):
    hubo_falla: bool
    descripcion: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validar_descripcion_si_hay_falla(self) -> "RegistrarFallaRequest":
        if self.hubo_falla and not (self.descripcion and self.descripcion.strip()):
            raise ValueError(
                "Se requiere una descripción cuando 'hubo_falla' es verdadero."
            )
        return self
```

## Métricas de Calidad y Arquitectura Global
- _Clean Architecture:_ Desacoplamiento total entre Routers (FastAPI), Servicios de Negocio, Repositorios (SQLAlchemy) y Modelos de Datos.

- _Pruebas Automatizadas:_ 46 pruebas unitarias e de integración con pytest y TestClient, manteniendo una cobertura global superior al 97%.

- _Tipado Estricto y Linting:_ Cero tolerancias a errores de tipo con mypy y cumplimiento estricto de estilo con ruff
"""Repositorio de Historial Global (app/repositories/historial_repository.py).

A diferencia de EquipoRepository/EstudianteRepository (que arman
historial ligado a un id concreto), este repositorio junta la
actividad de TODO el laboratorio para alimentar la pestaña "Historial"
sin requerir un filtro previo.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.labtrack import Equipo, Falla, Sesion, SesionEquipo


class HistorialRepository:
    def list_sesion_equipos(self, db: Session) -> list[SesionEquipo]:
        """Todos los préstamos registrados (cada uno trae su posible
        devolución), con equipo y estudiante precargados."""
        stmt = select(SesionEquipo).options(
            selectinload(SesionEquipo.equipo).selectinload(Equipo.tipo_equipo),
            selectinload(SesionEquipo.sesion).selectinload(Sesion.estudiante),
        )
        return list(db.execute(stmt).scalars().all())

    def list_fallas(self, db: Session) -> list[Falla]:
        """Todas las fallas registradas (cada una trae su posible
        resolución), con equipo precargado."""
        stmt = select(Falla).options(
            selectinload(Falla.equipo).selectinload(Equipo.tipo_equipo),
        )
        return list(db.execute(stmt).scalars().all())

"""Repositorio de Sesiones (app/repositories/sesion_repository.py)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.labtrack import Equipo, Sesion, SesionEquipo


class SesionRepository:
    def get_activa_by_estudiante(
        self, db: Session, estudiante_id: int
    ) -> Sesion | None:
        """Busca si el estudiante tiene una sesión que aún no ha sido cerrada."""
        stmt = select(Sesion).where(
            Sesion.estudiante_id == estudiante_id,
            Sesion.estado == "Activa"
        )
        return db.execute(stmt).scalar_one_or_none()

    def create(self, db: Session, estudiante_id: int) -> Sesion:
        """Crea una nueva sesión abierta para el estudiante."""
        nueva_sesion = Sesion(estudiante_id=estudiante_id, estado="Activa")
        db.add(nueva_sesion)
        db.commit()
        db.refresh(nueva_sesion)
        return nueva_sesion

    def add_equipo(self, db: Session, sesion_id: int, equipo: Equipo) -> SesionEquipo:
        """Agrega un equipo a la sesión y marca su estado como Prestado."""
        sesion_equipo = SesionEquipo(
            sesion_id=sesion_id,
            equipo_id=equipo.id,
            estado="Prestado"
        )
        
        # Actualizamos el estado del equipo en la misma transacción
        equipo.estado = "Prestado"
        
        db.add(sesion_equipo)
        db.commit()
        db.refresh(sesion_equipo)
        return sesion_equipo
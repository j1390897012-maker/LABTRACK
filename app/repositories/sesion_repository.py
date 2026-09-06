"""Repositorio de Sesiones (app/repositories/sesion_repository.py)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.labtrack import Sesion


class SesionRepository:
    def get_activa_by_estudiante(
        self, db: Session, estudiante_id: int
        ) -> Sesion | None:
        """Busca si el estudiante tiene una sesión que aún no ha sido cerrada."""
        stmt = select(Sesion).where(
            Sesion.estudiante_id == estudiante_id,
            Sesion.estado == "abierta"
        )
        return db.execute(stmt).scalar_one_or_none()

    def create(self, db: Session, estudiante_id: int) -> Sesion:
        """Crea una nueva sesión abierta para el estudiante."""
        nueva_sesion = Sesion(estudiante_id=estudiante_id, estado="abierta")
        db.add(nueva_sesion)
        db.commit()
        db.refresh(nueva_sesion)
        return nueva_sesion
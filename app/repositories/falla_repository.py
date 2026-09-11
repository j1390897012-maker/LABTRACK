"""Repositorio de Fallas (app/repositories/falla_repository.py)."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.labtrack import Equipo, Falla, Sesion, SesionEquipo


class FallaRepository:
    def get_by_id(self, db: Session, falla_id: int) -> Falla | None:
        """Busca una falla por su ID, con equipo y sesión/estudiante
        cargados para poder mostrar código y matrícula sin IDs internos."""
        stmt = (
            select(Falla)
            .where(Falla.id == falla_id)
            .options(
                selectinload(Falla.equipo).selectinload(Equipo.tipo_equipo),
                selectinload(Falla.sesion_equipo)
                .selectinload(SesionEquipo.sesion)
                .selectinload(Sesion.estudiante),
            )
        )
        return db.execute(stmt).scalar_one_or_none()

    def list_all(
        self,
        db: Session,
        estado: str | None = None,
    ) -> list[Falla]:
        """Lista fallas, opcionalmente filtradas por estado
        (p. ej. 'Pendiente'), más recientes primero."""
        stmt = (
            select(Falla)
            .options(
                selectinload(Falla.equipo).selectinload(Equipo.tipo_equipo),
                selectinload(Falla.sesion_equipo)
                .selectinload(SesionEquipo.sesion)
                .selectinload(Sesion.estudiante),
            )
            .order_by(Falla.fecha.desc())
        )
        if estado:
            stmt = stmt.where(Falla.estado == estado)
        return list(db.execute(stmt).scalars().all())

    def get_by_equipo(self, db: Session, equipo_id: int) -> list[Falla]:
        """Lista las fallas asociadas a un equipo, más recientes primero."""
        stmt = (
            select(Falla)
            .where(Falla.equipo_id == equipo_id)
            .order_by(Falla.fecha.desc())
        )
        return list(db.execute(stmt).scalars().all())

    def create(
        self,
        db: Session,
        equipo_id: int,
        sesion_equipo_id: int | None,
        descripcion: str,
    ) -> Falla:
        """Registra una nueva falla en el historial del equipo.

        La falla queda inicialmente en estado 'Pendiente' y nunca sobrescribe
        ni elimina fallas anteriores (US-08).
        """
        nueva_falla = Falla(
            equipo_id=equipo_id,
            sesion_equipo_id=sesion_equipo_id,
            descripcion=descripcion,
            estado="Pendiente",
        )
        db.add(nueva_falla)
        db.commit()
        db.refresh(nueva_falla)
        return nueva_falla

"""Repositorio de Fallas (app/repositories/falla_repository.py)."""

from sqlalchemy.orm import Session

from app.models.labtrack import Falla


class FallaRepository:
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

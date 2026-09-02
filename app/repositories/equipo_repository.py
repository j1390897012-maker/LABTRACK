from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Equipo, TipoEquipo


class EquipoRepository:
    def get_by_codigo(self, db: Session, codigo: str) -> Equipo | None:
        """Busca un equipo por su código físico."""
        stmt = select(Equipo).where(Equipo.codigo == codigo)
        return db.execute(stmt).scalar_one_or_none()

    def get_tipo_by_nombre(self, db: Session, nombre: str) -> TipoEquipo | None:
        """Busca un tipo de equipo por su nombre."""
        stmt = select(TipoEquipo).where(TipoEquipo.nombre == nombre)
        return db.execute(stmt).scalar_one_or_none()

    def create_tipo(self, db: Session, nombre: str) -> TipoEquipo:
        """Crea un nuevo tipo de equipo si no existe en el catálogo."""
        nuevo_tipo = TipoEquipo(nombre=nombre)
        db.add(nuevo_tipo)
        db.commit()
        db.refresh(nuevo_tipo)
        return nuevo_tipo

    def create(self, db: Session, codigo: str, tipo_equipo_id: int) -> Equipo:
        """Crea el equipo físico asociado a su tipo."""
        nuevo_equipo = Equipo(
            codigo=codigo,
            tipo_equipo_id=tipo_equipo_id
            # 'estado' toma "Disponible" automáticamente por el modelo
        )
        db.add(nuevo_equipo)
        db.commit()
        db.refresh(nuevo_equipo)
        return nuevo_equipo
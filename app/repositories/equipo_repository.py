from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Equipo, TipoAccesorio, TipoEquipo


class EquipoRepository:
    def get_by_codigo(self, db: Session, codigo: str) -> Equipo | None:
        """Busca un equipo por su código físico."""
        stmt = (
            select(Equipo)
            .where(Equipo.codigo == codigo)
            .options(selectinload(Equipo.tipo_equipo))
        )
        return db.execute(stmt).scalar_one_or_none()

    def search(
        self,
        db: Session,
        codigo: str | None = None,
        estado: str | None = None,
        tipo: str | None = None,
    ) -> list[Equipo]:
        """Lista equipos, opcionalmente filtrando por código (parcial),
        estado (exacto) y/o tipo (nombre exacto)."""
        stmt = select(Equipo).options(selectinload(Equipo.tipo_equipo))
        if codigo:
            stmt = stmt.where(Equipo.codigo.ilike(f"%{codigo}%"))
        if estado:
            stmt = stmt.where(Equipo.estado == estado)
        if tipo:
            stmt = stmt.join(TipoEquipo).where(TipoEquipo.nombre == tipo)
        stmt = stmt.order_by(Equipo.codigo)
        return list(db.execute(stmt).scalars().all())

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

    def get_by_id(self, db: Session, equipo_id: int) -> Equipo | None:
        """Busca un equipo por su ID interno (Primary Key)."""
        stmt = select(Equipo).where(Equipo.id == equipo_id)
        return db.execute(stmt).scalar_one_or_none()

    def actualizar_estado(self, db: Session, equipo: Equipo, estado: str) -> Equipo:
        """Actualiza el estado general del equipo (p. ej. Disponible, En revisión)."""
        equipo.estado = estado
        db.commit()
        db.refresh(equipo)
        return equipo

    def list_tipos_equipo(self, db: Session) -> list[TipoEquipo]:
        """Lista el catálogo de tipos de equipo."""
        stmt = select(TipoEquipo).order_by(TipoEquipo.nombre)
        return list(db.execute(stmt).scalars().all())

    def obtener_todos(self, db: Session) -> list[Equipo]:
        """Lista todos los equipos ordenados por código."""
        stmt = (
            select(Equipo)
            .options(selectinload(Equipo.tipo_equipo))
            .order_by(Equipo.codigo)
        )
        return list(db.execute(stmt).scalars().all())

    def list_tipos_accesorio(
        self,
        db: Session,
        tipo_equipo_id: int | None = None,
    ) -> list[TipoAccesorio]:
        """Lista el catálogo de tipos de accesorio, opcionalmente filtrado
        por tipo de equipo."""
        stmt = select(TipoAccesorio)
        if tipo_equipo_id is not None:
            stmt = stmt.where(TipoAccesorio.tipo_equipo_id == tipo_equipo_id)
        stmt = stmt.order_by(TipoAccesorio.nombre)
        return list(db.execute(stmt).scalars().all())
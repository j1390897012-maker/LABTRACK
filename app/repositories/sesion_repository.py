"""Repositorio de Sesiones (app/repositories/sesion_repository.py)."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.labtrack import Equipo, Sesion, SesionEquipo, SesionEquipoAccesorio


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

    def get_prestamo_activo_by_equipo(
        self,
        db: Session,
        equipo_id: int,
    ) -> SesionEquipo | None:
        """Busca el préstamo activo asociado a un equipo."""
        stmt = select(SesionEquipo).where(
        SesionEquipo.equipo_id == equipo_id,
        SesionEquipo.estado == "Prestado"
    )
        return db.execute(stmt).scalar_one_or_none()

    def get_sesiones_activas(
    self, db: Session,
    )-> list[Sesion]:
        """ Obtiene todas las sesiones que permanecen activas"""
        stmt = select(Sesion).where(
        Sesion.estado == "Activa"
    )
        return list(db.execute(stmt).scalars().all())

    def add_accesorios_prestamo(
        self, 
        db: Session, 
        sesion_equipo_id: int, 
        accesorios: list[dict[str, int]]
    ) -> None:
        """Registra los accesorios vinculados a un préstamo de equipo (US-04)."""
        for acc in accesorios:
            nuevo_accesorio = SesionEquipoAccesorio(
                sesion_equipo_id=sesion_equipo_id,
                tipo_accesorio_id=acc["tipo_accesorio_id"],
                cantidad_prestada=acc["cantidad"]
            )
            db.add(nuevo_accesorio)
        db.commit()


    def get_accesorio_prestamo(
        self,
        db: Session,
        sesion_equipo_id: int,
        tipo_accesorio_id: int,
    ) -> SesionEquipoAccesorio | None:
        """Busca un accesorio específico dentro de un préstamo."""
        stmt = select(SesionEquipoAccesorio).where(
            SesionEquipoAccesorio.sesion_equipo_id == sesion_equipo_id,
            SesionEquipoAccesorio.tipo_accesorio_id == tipo_accesorio_id,
        )
        return db.execute(stmt).scalar_one_or_none()

    def actualizar_cantidad_devuelta(
        self,
        db: Session,
        accesorio: SesionEquipoAccesorio,
        cantidad_devuelta: int,
    ) -> SesionEquipoAccesorio:
        """Actualiza la cantidad de accesorios devueltos."""
        accesorio.cantidad_devuelta = cantidad_devuelta
        db.commit()
        db.refresh(accesorio)
        return accesorio

    def get_sesion_equipo_by_id(
        self,
        db: Session,
        sesion_equipo_id: int,
    ) -> SesionEquipo | None:
        """Busca un préstamo de equipo por su ID."""
        return db.get(SesionEquipo, sesion_equipo_id)

    def get_equipos_by_sesion(self, db: Session, sesion_id: int) -> list[SesionEquipo]:
        """Obtiene todos los equipos vinculados a una sesión."""
        stmt = (
            select(SesionEquipo)
            .where(SesionEquipo.sesion_id == sesion_id)
            .options(selectinload(SesionEquipo.equipo))
        )
        return list(db.execute(stmt).scalars().all())

    def get_equipos_prestados_by_sesion(
        self, db: Session, sesion_id: int
    ) -> list[SesionEquipo]:
        """Obtiene los equipos actualmente prestados (no devueltos) de una
        sesión."""
        stmt = (
            select(SesionEquipo)
            .where(
                SesionEquipo.sesion_id == sesion_id,
                SesionEquipo.estado == "Prestado",
            )
            .options(selectinload(SesionEquipo.equipo))
        )
        return list(db.execute(stmt).scalars().all())

    def get_historial_by_equipo(
        self, db: Session, equipo_id: int
    ) -> list[SesionEquipo]:
        """Obtiene el historial completo de préstamos de un equipo
        (sesión, estudiante, accesorios y fallas), ordenado por fecha de
        préstamo descendente (US-10)."""
        stmt = (
            select(SesionEquipo)
            .where(SesionEquipo.equipo_id == equipo_id)
            .options(
                selectinload(SesionEquipo.sesion).selectinload(Sesion.estudiante),
                selectinload(SesionEquipo.accesorios).selectinload(
                    SesionEquipoAccesorio.tipo_accesorio
                ),
                selectinload(SesionEquipo.fallas),
            )
            .order_by(SesionEquipo.fecha_prestamo.desc())
        )
        return list(db.execute(stmt).scalars().all())

    def obtener_todos(self, db: Session):
        return db.query(Equipo).all()

    def cerrar_sesion(self, db: Session, sesion: Sesion) -> Sesion:
        """Actualiza el estado de la sesión a Cerrada."""
        sesion.estado = "Cerrada"
        db.commit()
        db.refresh(sesion)
        return sesion

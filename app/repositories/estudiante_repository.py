"""Repositorio de Estudiantes (app/repositories/estudiante_repository.py)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Estudiante


class EstudianteRepository:
    def get_by_rfid(self, db: Session, uid_rfid: str) -> Estudiante | None:
        stmt = select(Estudiante).where(Estudiante.uid_rfid == uid_rfid)
        return db.execute(stmt).scalar_one_or_none()

    def get_by_matricula(self, db: Session, matricula: str) -> Estudiante | None:
        stmt = select(Estudiante).where(Estudiante.matricula == matricula)
        return db.execute(stmt).scalar_one_or_none()

    def get_by_id(self, db: Session, estudiante_id: int) -> Estudiante | None:
        return db.get(Estudiante, estudiante_id)

    def asignar_rfid(self, db: Session, 
        estudiante_id: int, uid_rfid: str) -> Estudiante:
        estudiante = db.get(Estudiante, estudiante_id)
        if not estudiante:
            raise ValueError(f"Estudiante con ID {estudiante_id} no encontrado")
        estudiante.uid_rfid = uid_rfid
        db.commit()
        db.refresh(estudiante)
        return estudiante

    def create(self, db: Session, nombre: str, matricula: str) -> Estudiante:
        nuevo_estudiante = Estudiante(
            nombre=nombre,
            matricula=matricula
        )
        db.add(nuevo_estudiante)
        db.commit()
        db.refresh(nuevo_estudiante)
        return nuevo_estudiante
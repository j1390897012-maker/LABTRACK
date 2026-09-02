"""
Servicio de Equipos (app/services/equipo_service.py)

Contiene la lógica de negocio central de la US-01.
Se encarga de orquestar las operaciones entre la base de datos (Repository) 
y las validaciones de entrada. Su función principal aquí es:
- Comprobar que no existan equipos con códigos duplicados.
- Si el código existe, lanza un error HTTP 409 (Conflicto).
- Si no existe, delega la creación del tipo de equipo 
  y del equipo físico al Repositorio.
"""

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.equipo_repository import EquipoRepository
from app.schemas.equipo import EquipoCreate


class EquipoService:
    def __init__(self) -> None:
        self.repo = EquipoRepository()

    def registrar_equipo(self, db: Session, equipo_in: EquipoCreate) -> dict[str, Any]:
        # 1. Verificar si el código ya está registrado
        equipo_existente = self.repo.get_by_codigo(db, equipo_in.codigo)
        if equipo_existente:
            # Lanza un error HTTP 409 si se intenta registrar un código repetido
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail="El dispositivo ya se encuentra registrado"
            )

        # 2. Buscar el tipo de equipo o crearlo si es nuevo
        tipo = self.repo.get_tipo_by_nombre(db, equipo_in.tipo)
        if not tipo:
            tipo = self.repo.create_tipo(db, equipo_in.tipo)

        # 3. Crear el equipo físico
        nuevo_equipo = self.repo.create(db, equipo_in.codigo, tipo.id)

        # 4. Devolver los datos formateados para que coincidan con EquipoOut
        return {
            "id": nuevo_equipo.id,
            "codigo": nuevo_equipo.codigo,
            "estado": nuevo_equipo.estado,
            "tipo": tipo.nombre
        }
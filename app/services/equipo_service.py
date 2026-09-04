import base64
from io import BytesIO
from typing import Any

import qrcode
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.equipo_repository import EquipoRepository
from app.schemas.equipo import EquipoCreate


class EquipoService:
    def __init__(self) -> None:
        self.repo = EquipoRepository()

    def registrar_equipo(self, db: Session, equipo_in: EquipoCreate) -> dict[str, Any]:
        # 1. Verificar duplicados
        equipo_existente = self.repo.get_by_codigo(db, equipo_in.codigo)
        if equipo_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail="El dispositivo ya se encuentra registrado"
            )

        # 2. Buscar o crear tipo
        tipo = self.repo.get_tipo_by_nombre(db, equipo_in.tipo)
        if not tipo:
            tipo = self.repo.create_tipo(db, equipo_in.tipo)

        # 3. Crear equipo físico
        nuevo_equipo = self.repo.create(db, equipo_in.codigo, tipo.id)

        # 4. Generar el código QR en memoria (Base64)
        qr = qrcode.make(nuevo_equipo.codigo)
        buffer = BytesIO()
        qr.save(buffer)
        qr_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        qr_data_uri = f"data:image/png;base64,{qr_b64}"

        # 5. Devolver los datos
        return {
            "id": nuevo_equipo.id,
            "codigo": nuevo_equipo.codigo,
            "estado": nuevo_equipo.estado,
            "tipo": tipo.nombre,
            "qr_base64": qr_data_uri
        }
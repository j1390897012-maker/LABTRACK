import base64
from io import BytesIO
from typing import Any

import qrcode
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.equipo_repository import EquipoRepository
from app.schemas.equipo import EquipoCreate
from app.schemas.historial_equipo import (
    HistorialEquipoResponse,
    HistorialFallaEquipo,
    HistorialUsoEquipo,
)


class EquipoService:
    repo: EquipoRepository

    def __init__(self) -> None:
        self.repo = EquipoRepository()
        # Aliamos ambos nombres por compatibilidad con los dos métodos
        self.repo_equipo = self.repo

    def registrar_equipo(self, db: Session, equipo_in: EquipoCreate) -> dict[str, Any]:
        """Registra un nuevo equipo físico en el sistema."""
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

    def obtener_historial(self, db: Session, equipo_id: int) -> HistorialEquipoResponse:
        """Consulta el historial completo de un equipo (US-10)."""
        equipo = self.repo_equipo.get_historial_completo(db, equipo_id)
        
        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Equipo no encontrado."
            )

        usos = []
        for prestamo in sorted(
            equipo.sesion_equipos,
            key=lambda p: p.fecha_prestamo,
            reverse=True
        ):
            estudiante = (
                prestamo.sesion.estudiante
                if prestamo.sesion and prestamo.sesion.estudiante
                else None
            )

            fallas = [
                HistorialFallaEquipo(
                    id=f.id,
                    descripcion=f.descripcion,
                    estado=f.estado,
                    fecha=f.fecha
                ) for f in prestamo.fallas
            ]

            nombre_est = (
                estudiante.nombre if estudiante and estudiante.nombre else "Desconocido"
            )
            mat_est = (
                estudiante.matricula if estudiante and estudiante.matricula else "N/A"
            )

            usos.append(
                HistorialUsoEquipo(
                    sesion_equipo_id=prestamo.id,
                    estudiante_nombre=nombre_est,
                    matricula_estudiante=mat_est,
                    estado_prestamo=prestamo.estado,
                    fecha_prestamo=prestamo.fecha_prestamo,
                    fecha_devolucion=prestamo.fecha_devolucion,
                    fallas=fallas
                )
            )

        return HistorialEquipoResponse(
            equipo_id=equipo.id,
            codigo=equipo.codigo,
            tipo=equipo.tipo_equipo.nombre if equipo.tipo_equipo else "Sin tipo",
            estado_actual=equipo.estado,
            historial_usos=usos
        )

    def obtener_historial_por_codigo(
        self, db: Session, codigo: str
    ) -> HistorialEquipoResponse:
        """Busca el equipo por su código físico (QR) para obtener su ID 
        y delega en la consulta de historial (US-10).
        """
        equipo = self.repo.get_by_codigo(db, codigo)
        
        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Equipo no encontrado.",
            )
            
        return self.obtener_historial(db, equipo.id)
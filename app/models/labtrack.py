from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class TipoEquipo(Base):
    """ Modelo para representar los tipos de equipos """
    __tablename__ = "tipos_equipo"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)

    equipos: Mapped[list["Equipo"]] = relationship(
        back_populates="tipo_equipo",
    )
    tipos_accesorio: Mapped[list["TipoAccesorio"]] = relationship(
        back_populates="tipo_equipo",
    )


class TipoAccesorio(Base):
    """ Modelo para representar los tipos de accesorios """
    __tablename__ = "tipos_accesorio"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo_equipo_id: Mapped[int] = mapped_column(
        ForeignKey("tipos_equipo.id"),
    )
    nombre: Mapped[str] = mapped_column(String(100))
    cantidad_default: Mapped[int] = mapped_column(default=1)

    tipo_equipo: Mapped["TipoEquipo"] = relationship(
        back_populates="tipos_accesorio",
    )
    sesion_equipo_accesorios: Mapped[
        list["SesionEquipoAccesorio"]
    ] = relationship(
        back_populates="tipo_accesorio",
    )


class Estudiante(Base):
    """ Modelo para representar los estudiantes """

    __tablename__ = "estudiantes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150))
    matricula: Mapped[str] = mapped_column(
        String(50),
        unique=True,
    )
    foto: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    uid_rfid: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
    )

    sesiones: Mapped[list["Sesion"]] = relationship(
        back_populates="estudiante",
    )


class Equipo(Base):
    """ Modelo para representar los equipos """

    __tablename__ = "equipos"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(
        String(50),
        unique=True,
    )
    tipo_equipo_id: Mapped[int] = mapped_column(
        ForeignKey("tipos_equipo.id"),
    )
    estado: Mapped[str] = mapped_column(
        String(30),
        default="Disponible",
    )

    tipo_equipo: Mapped["TipoEquipo"] = relationship(
        back_populates="equipos",
    )
    sesion_equipos: Mapped[list["SesionEquipo"]] = relationship(
        back_populates="equipo",
    )
    fallas: Mapped[list["Falla"]] = relationship(
        back_populates="equipo",
    )


class Sesion(Base):
    __tablename__ = "sesiones"

    id: Mapped[int] = mapped_column(primary_key=True)
    estudiante_id: Mapped[int] = mapped_column(
        ForeignKey("estudiantes.id"),
    )
    estado: Mapped[str] = mapped_column(
        String(30),
        default="Activa",
    )
    fecha_apertura: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
    )
    fecha_cierre: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )

    estudiante: Mapped["Estudiante"] = relationship(
        back_populates="sesiones",
    )
    sesion_equipos: Mapped[list["SesionEquipo"]] = relationship(
        back_populates="sesion",
    )


class SesionEquipo(Base):
    __tablename__ = "sesion_equipos"

    id: Mapped[int] = mapped_column(primary_key=True)
    sesion_id: Mapped[int] = mapped_column(
        ForeignKey("sesiones.id"),
    )
    equipo_id: Mapped[int] = mapped_column(
        ForeignKey("equipos.id"),
    )
    fecha_prestamo: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
    )
    fecha_devolucion: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
    estado: Mapped[str] = mapped_column(
        String(30),
        default="Prestado",
    )

    sesion: Mapped["Sesion"] = relationship(
        back_populates="sesion_equipos",
    )
    equipo: Mapped["Equipo"] = relationship(
        back_populates="sesion_equipos",
    )
    accesorios: Mapped[
        list["SesionEquipoAccesorio"]
    ] = relationship(
        back_populates="sesion_equipo",
    )
    fallas: Mapped[list["Falla"]] = relationship(
        back_populates="sesion_equipo",
    )


class SesionEquipoAccesorio(Base):
    __tablename__ = "sesion_equipo_accesorios"

    id: Mapped[int] = mapped_column(primary_key=True)
    sesion_equipo_id: Mapped[int] = mapped_column(
        ForeignKey("sesion_equipos.id"),
    )
    tipo_accesorio_id: Mapped[int] = mapped_column(
        ForeignKey("tipos_accesorio.id"),
    )
    cantidad_prestada: Mapped[int] = mapped_column()
    cantidad_devuelta: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    sesion_equipo: Mapped["SesionEquipo"] = relationship(
        back_populates="accesorios",
    )
    tipo_accesorio: Mapped["TipoAccesorio"] = relationship(
        back_populates="sesion_equipo_accesorios",
    )


class Falla(Base):
    __tablename__ = "fallas"

    id: Mapped[int] = mapped_column(primary_key=True)
    equipo_id: Mapped[int] = mapped_column(
        ForeignKey("equipos.id"),
    )
    sesion_equipo_id: Mapped[int | None] = mapped_column(
        ForeignKey("sesion_equipos.id"),
        nullable=True,
    )
    descripcion: Mapped[str] = mapped_column(Text)
    fecha: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
    )
    estado: Mapped[str] = mapped_column(
        String(30),
        default="Pendiente",
    )
    fecha_resolucion: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
    observacion_resolucion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    equipo: Mapped["Equipo"] = relationship(
        back_populates="fallas",
    )
    sesion_equipo: Mapped["SesionEquipo | None"] = relationship(
        back_populates="fallas",
    )
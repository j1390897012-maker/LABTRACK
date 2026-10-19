"""agregar datos de inventario a equipos

Revision ID: 7d1e4b9a2f10
Revises: 3c62c2b3a110
Create Date: 2026-10-16 15:40:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7d1e4b9a2f10"
down_revision: str | Sequence[str] | None = "3c62c2b3a110"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Agrega numero_inventario, marca y modelo (todas opcionales, así que
    los equipos ya registrados en producción no se ven afectados)."""
    op.add_column(
        "equipos",
        sa.Column("numero_inventario", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "equipos",
        sa.Column("marca", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "equipos",
        sa.Column("modelo", sa.String(length=100), nullable=True),
    )
    # Mismo nombre que genera SQLAlchemy para `unique=True, index=True` en el
    # modelo, así el esquema creado por la migración es idéntico al de
    # `Base.metadata.create_all` (verificado comparando ambos).
    op.create_index(
        "ix_equipos_numero_inventario",
        "equipos",
        ["numero_inventario"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_equipos_numero_inventario", table_name="equipos")
    op.drop_column("equipos", "modelo")
    op.drop_column("equipos", "marca")
    op.drop_column("equipos", "numero_inventario")

from sqlalchemy.orm import Session

from app.repositories.equipo_repository import EquipoRepository
from app.schemas.catalogo import TipoAccesorioOut, TipoEquipoOut


class CatalogoService:
    def __init__(self) -> None:
        self.repo_equipo = EquipoRepository()

    def listar_tipos_equipo(self, db: Session) -> list[TipoEquipoOut]:
        tipos = self.repo_equipo.list_tipos_equipo(db)
        return [TipoEquipoOut.model_validate(t) for t in tipos]

    def listar_tipos_accesorio(
        self, db: Session, tipo_equipo_id: int | None = None
    ) -> list[TipoAccesorioOut]:
        tipos = self.repo_equipo.list_tipos_accesorio(db, tipo_equipo_id=tipo_equipo_id)
        return [TipoAccesorioOut.model_validate(t) for t in tipos]

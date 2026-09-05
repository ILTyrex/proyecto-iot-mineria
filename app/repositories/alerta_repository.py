from typing import List
from sqlalchemy.orm import Session

from app.models.alerta import Alerta
from app.repositories.base_repository import BaseRepository


class AlertaRepository(BaseRepository[Alerta]):
    def __init__(self, db: Session):
        super().__init__(Alerta, db)

    def listar_no_atendidas(self, skip: int = 0, limit: int = 100) -> List[Alerta]:
        return (
            self.db.query(Alerta)
            .filter(Alerta.atendida.is_(False))
            .order_by(Alerta.fecha_creacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

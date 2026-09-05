from typing import Optional
from sqlalchemy.orm import Session

from app.models.dispositivo import Dispositivo
from app.repositories.base_repository import BaseRepository


class DispositivoRepository(BaseRepository[Dispositivo]):
    def __init__(self, db: Session):
        super().__init__(Dispositivo, db)

    def get_by_codigo(self, codigo: str) -> Optional[Dispositivo]:
        return self.db.query(Dispositivo).filter(Dispositivo.codigo == codigo).first()

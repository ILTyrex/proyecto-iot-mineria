from typing import Optional
from sqlalchemy.orm import Session

from app.models.sensor import Sensor
from app.repositories.base_repository import BaseRepository


class SensorRepository(BaseRepository[Sensor]):
    def __init__(self, db: Session):
        super().__init__(Sensor, db)

    def get_by_nombre(self, nombre: str) -> Optional[Sensor]:
        return self.db.query(Sensor).filter(Sensor.nombre == nombre).first()

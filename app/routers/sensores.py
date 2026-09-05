from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.sensor import Sensor
from app.schemas.sensor import SensorOut

router = APIRouter(prefix="/api/sensores", tags=["Sensores"])


@router.get("/", response_model=List[SensorOut])
def listar_sensores(db: Session = Depends(get_db)):
    return db.query(Sensor).all()

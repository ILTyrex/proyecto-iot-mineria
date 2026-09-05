"""
Servicio con la lógica de negocio principal:
  - Clasifica la lectura según la escala de calidad del aire (CO2 ppm).
  - Registra la lectura en la base de datos (hypertable TimescaleDB).
  - Genera una alerta automática si la calidad es "Mala" o "Peligrosa".
  - Deja un registro en la bitácora (logs_sistema).
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.nivel_calidad import NivelCalidadAire
from app.models.alerta import Alerta
from app.models.log_sistema import LogSistema
from app.repositories.dispositivo_repository import DispositivoRepository
from app.repositories.lectura_repository import LecturaRepository

NIVELES_CRITICOS = ("Mala", "Peligrosa")


class LecturaService:
    def __init__(self, db: Session):
        self.db = db
        self.lectura_repo = LecturaRepository(db)
        self.dispositivo_repo = DispositivoRepository(db)

    def _clasificar_nivel(self, co2_ppm: float) -> "NivelCalidadAire | None":
        nivel = (
            self.db.query(NivelCalidadAire)
            .filter(NivelCalidadAire.ppm_min <= co2_ppm, NivelCalidadAire.ppm_max > co2_ppm)
            .first()
        )
        if not nivel:
            # Si supera el máximo de todos los rangos, se asigna el más alto (Peligrosa)
            nivel = self.db.query(NivelCalidadAire).order_by(NivelCalidadAire.ppm_max.desc()).first()
        return nivel

    def registrar_lectura(self, codigo_dispositivo: str, temperatura: float, humedad: float, co2_ppm: float):
        dispositivo = self.dispositivo_repo.get_by_codigo(codigo_dispositivo)
        if not dispositivo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dispositivo '{codigo_dispositivo}' no está registrado en el sistema",
            )
        if not dispositivo.activo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"El dispositivo '{codigo_dispositivo}' está inactivo",
            )

        nivel = self._clasificar_nivel(co2_ppm)

        lectura = self.lectura_repo.create({
            "dispositivo_id": dispositivo.id,
            "temperatura": temperatura,
            "humedad": humedad,
            "co2_ppm": co2_ppm,
            "nivel_calidad_id": nivel.id if nivel else None,
        })

        if nivel and nivel.nombre in NIVELES_CRITICOS:
            alerta = Alerta(
                lectura_id=lectura.id,
                lectura_timestamp=lectura.timestamp,
                tipo_alerta="calidad_aire",
                mensaje=f"Nivel de calidad del aire: {nivel.nombre} ({co2_ppm:.0f} ppm)",
            )
            self.db.add(alerta)

        log = LogSistema(
            dispositivo_id=dispositivo.id,
            evento="lectura_recibida",
            detalle=f"T={temperatura}°C H={humedad}% CO2={co2_ppm}ppm",
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(lectura)
        return lectura

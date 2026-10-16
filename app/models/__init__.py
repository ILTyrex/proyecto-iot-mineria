# Importa todos los modelos para que SQLAlchemy conozca las relaciones
# al llamar Base.metadata.create_all()
from app.models.ubicacion import Ubicacion
from app.models.tipo_alerta import TipoAlerta
from app.models.dispositivo import Dispositivo
from app.models.sensor import Sensor
from app.models.dispositivo_sensor import DispositivoSensor
from app.models.nivel_calidad import NivelCalidadAire
from app.models.lectura import Lectura
from app.models.alerta import Alerta
from app.models.usuario import Usuario
from app.models.log_sistema import LogSistema

__all__ = [
    "Ubicacion",
    "TipoAlerta",
    "Dispositivo",
    "Sensor",
    "DispositivoSensor",
    "NivelCalidadAire",
    "Lectura",
    "Alerta",
    "Usuario",
    "LogSistema",
]
"""
Seguridad básica de la API mediante API Key.
El ESP32 debe enviar el header:  X-API-Key: <valor definido en .env>
"""
from fastapi import Header, HTTPException, status

from app.core.config import settings


def verificar_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> bool:
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida o no proporcionada",
        )
    return True

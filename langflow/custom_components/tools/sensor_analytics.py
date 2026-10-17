from __future__ import annotations

import os
from collections import defaultdict
from datetime import datetime, timezone
from statistics import fmean, stdev
from typing import Any

import requests
from lfx.custom import Component
from lfx.io import MessageTextInput, Output
from lfx.schema import Data


METRICS = ("temperatura", "humedad", "co2_ppm")
PAGE_SIZE = 1000


class SensorAnalytics(Component):
    display_name = "Sensor Analytics"
    description = "Calcula descripciones, comparaciones y tendencias desde las lecturas de la API."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "chart-no-axes-combined"
    name = "SensorAnalytics"

    inputs = [
        MessageTextInput(
            name="question",
            display_name="Pregunta",
            info="Pregunta analitica que el agente desea responder con las lecturas.",
            tool_mode=True,
        )
    ]
    outputs = [Output(name="analysis", display_name="Analisis", method="analyze")]

    def _load_readings(self) -> list[dict[str, Any]]:
        api_url = os.getenv("SENSOR_API_URL", "http://localhost:8000").rstrip("/")
        endpoint = f"{api_url}/api/lecturas/"
        readings: list[dict[str, Any]] = []
        skip = 0

        while True:
            response = requests.get(
                endpoint,
                params={"skip": skip, "limit": PAGE_SIZE},
                timeout=30,
            )
            response.raise_for_status()
            page = response.json()
            if not isinstance(page, list):
                raise ValueError("La API devolvio un formato de lecturas no valido.")
            readings.extend(page)
            if len(page) < PAGE_SIZE:
                break
            skip += len(page)

        return readings

    @staticmethod
    def _timestamp(reading: dict[str, Any]) -> datetime:
        value = str(reading["timestamp"]).replace("Z", "+00:00")
        timestamp = datetime.fromisoformat(value)
        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=timezone.utc)
        return timestamp.astimezone(timezone.utc)

    @staticmethod
    def _averages(readings: list[dict[str, Any]]) -> dict[str, float | None]:
        return {
            metric: round(fmean(float(row[metric]) for row in readings), 2)
            if readings
            else None
            for metric in METRICS
        }

    @staticmethod
    def _stats(values: list[float]) -> dict[str, float | None]:
        if not values:
            return {"promedio": None, "minimo": None, "maximo": None, "desviacion": None}
        return {
            "promedio": round(fmean(values), 2),
            "minimo": round(min(values), 2),
            "maximo": round(max(values), 2),
            "desviacion": round(stdev(values), 2) if len(values) > 1 else 0.0,
        }

    def analyze(self) -> Data:
        readings = self._load_readings()
        if not readings:
            raise ValueError("La API no contiene lecturas para analizar.")

        readings.sort(key=self._timestamp)
        parsed = [(row, self._timestamp(row)) for row in readings]
        by_device: dict[str, list[dict[str, Any]]] = defaultdict(list)
        by_day: dict[str, list[dict[str, Any]]] = defaultdict(list)
        quality_counts: dict[str, int] = defaultdict(int)

        for row, timestamp in parsed:
            by_device[str(row.get("dispositivo") or "Sin dispositivo")].append(row)
            by_day[timestamp.date().isoformat()].append(row)
            quality_counts[str(row.get("nivel_calidad") or "Sin clasificar")] += 1

        first_half = readings[: len(readings) // 2]
        second_half = readings[len(readings) // 2 :]
        half_size = max(1, min(7, len(by_day) // 2))
        daily_keys = sorted(by_day)[-60:]
        daily_trend = [
            {
                "fecha": day,
                "lecturas": len(by_day[day]),
                "promedios": self._averages(by_day[day]),
            }
            for day in daily_keys
        ]

        trends: dict[str, dict[str, Any]] = {}
        for metric in METRICS:
            values = [point["promedios"][metric] for point in daily_trend]
            if len(values) < 2:
                direction = "insuficientes_datos"
                change = None
            else:
                start_average = fmean(values[:half_size])
                end_average = fmean(values[-half_size:])
                change = round((end_average - start_average) / abs(start_average) * 100, 2) if start_average else None
                direction = "estable" if change is None or abs(change) < 1 else "ascendente" if change > 0 else "descendente"
            trends[metric] = {"direccion": direction, "cambio_porcentual": change}

        period_comparison: dict[str, Any] = {
            "primer_periodo": {
                "desde": self._timestamp(first_half[0]).date().isoformat(),
                "hasta": self._timestamp(first_half[-1]).date().isoformat(),
                "promedios": self._averages(first_half),
            },
            "segundo_periodo": {
                "desde": self._timestamp(second_half[0]).date().isoformat(),
                "hasta": self._timestamp(second_half[-1]).date().isoformat(),
                "promedios": self._averages(second_half),
            },
        }

        summary = {
            "pregunta": str(getattr(self.question, "text", self.question)),
            "total_lecturas": len(readings),
            "periodo": {
                "desde": self._timestamp(readings[0]).isoformat(),
                "hasta": self._timestamp(readings[-1]).isoformat(),
            },
            "variables": {
                metric: self._stats([float(row[metric]) for row in readings])
                for metric in METRICS
            },
            "dispositivos": {
                device: {
                    "lecturas": len(rows),
                    "promedios": self._averages(rows),
                }
                for device, rows in sorted(by_device.items())
            },
            "niveles_calidad": dict(sorted(quality_counts.items())),
            "comparacion_temporal": period_comparison,
            "tendencias_diarias_ultimos_60_dias": daily_trend,
            "tendencia": trends,
        }
        self.status = f"Analizadas {len(readings)} lecturas."
        return Data(data=summary)

from __future__ import annotations

from datetime import datetime

import pandas as pd
import requests
import streamlit as st

from data.openaq_client import CIDADES_ALVO, COORDENADAS, ESTADOS

BASE_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
HOURLY_PARAMS = "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone"
TIMEZONE = "America/Sao_Paulo"
START_DATE = "2025-01-01"


@st.cache_data(ttl=3600)
def carregar_dados() -> pd.DataFrame:
    """Busca dados reais via Open-Meteo e retorna DataFrame diário."""
    all_rows: list[pd.DataFrame] = []
    end_date = datetime.now().date().isoformat()

    for cidade in CIDADES_ALVO:
        lat, lon = COORDENADAS[cidade]
        try:
            resp = requests.get(
                BASE_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "start_date": START_DATE,
                    "end_date": end_date,
                    "hourly": HOURLY_PARAMS,
                    "timezone": TIMEZONE,
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException:
            continue

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        if not times:
            continue

        df = pd.DataFrame(
            {
                "data": times,
                "pm25": hourly.get("pm2_5", []),
                "pm10": hourly.get("pm10", []),
                "no2": hourly.get("nitrogen_dioxide", []),
                "co": hourly.get("carbon_monoxide", []),
                "o3": hourly.get("ozone", []),
            }
        )
        df["data"] = pd.to_datetime(df["data"])
        df = df.groupby(df["data"].dt.date, as_index=False).mean()
        df["data"] = pd.to_datetime(df["data"])
        df["cidade"] = cidade
        df["estado"] = ESTADOS[cidade]
        df["latitude"] = lat
        df["longitude"] = lon
        df = df[["data", "cidade", "estado", "latitude", "longitude", "pm25", "pm10", "no2", "co", "o3"]]
        all_rows.append(df)

    if not all_rows:
        return pd.DataFrame(
            columns=["data", "cidade", "estado", "latitude", "longitude", "pm25", "pm10", "no2", "co", "o3"]
        )

    return pd.concat(all_rows, ignore_index=True)

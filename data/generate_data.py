"""
Geração de dados simulados realistas de qualidade do ar para o Brasil — 2024.

Execute este script diretamente para gerar/atualizar data/ar_brasil.parquet:
    python data/generate_data.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

np.random.seed(42)

# Cidades: nome → (estado, latitude, longitude)

CIDADES: dict[str, tuple[str, float, float]] = {
    "São Paulo":      ("SP", -23.5505, -46.6333),
    "Rio de Janeiro": ("RJ", -22.9068, -43.1729),
    "Belo Horizonte": ("MG", -19.9167, -43.9345),
    "Curitiba":       ("PR", -25.4297, -49.2711),
    "Porto Alegre":   ("RS", -30.0346, -51.2177),
    "Salvador":       ("BA", -12.9714, -38.5014),
    "Recife":         ("PE",  -8.0476, -34.8770),
    "Manaus":         ("AM",  -3.1190, -60.0217),
    "Fortaleza":      ("CE",  -3.7172, -38.5433),
    "Brasília":       ("DF", -15.7801, -47.9292),
}

dates = pd.date_range("2025-01-01", pd.Timestamp.today().normalize(), freq="D")


def _iqa_de_pm25(pm25: float) -> int:
    """Calcula IQA a partir do PM2.5 conforme faixas CONAMA (interpolação linear)."""
    if pm25 < 25:
        return int((pm25 / 25.0) * 50)
    elif pm25 < 50:
        return int(51 + ((pm25 - 25) / 25.0) * 49)
    elif pm25 < 75:
        return int(101 + ((pm25 - 50) / 25.0) * 49)
    elif pm25 < 125:
        return int(151 + ((pm25 - 75) / 50.0) * 49)
    else:
        return min(500, int(201 + ((pm25 - 125) / 125.0) * 299))


def _sazonalidade_inverno(month: int, intensidade: float = 0.35) -> float:
    """Fator multiplicador com pico em julho (inverno no hemisfério sul)."""
    return 1.0 + intensidade * np.exp(-((month - 7) ** 2) / 4.0)


def _sazonalidade_queimadas(month: int) -> float:
    """Fator para queimadas amazônicas: pico em outubro (set–nov)."""
    return 1.0 + 3.5 * np.exp(-((month - 10) ** 2) / 3.0)


rows: list[dict] = []

for cidade, (estado, lat, lon) in CIDADES.items():
    for date in dates:
        month = date.month

        # ------------------------------------------------------------------
        # PM2.5 — base + sazonalidade + ruído lognormal
        # ------------------------------------------------------------------
        if cidade == "São Paulo":
            pm25_base = 30.0
            fator = _sazonalidade_inverno(month, 0.38)
        elif cidade == "Rio de Janeiro":
            pm25_base = 26.0
            fator = _sazonalidade_inverno(month, 0.32)
        elif cidade == "Belo Horizonte":
            pm25_base = 20.0
            fator = _sazonalidade_inverno(month, 0.35)
        elif cidade == "Curitiba":
            pm25_base = 17.0
            fator = _sazonalidade_inverno(month, 0.50)   # inversão térmica acentuada
        elif cidade == "Porto Alegre":
            pm25_base = 17.0
            fator = _sazonalidade_inverno(month, 0.48)   # inversão térmica acentuada
        elif cidade == "Manaus":
            pm25_base = 14.0
            fator = _sazonalidade_queimadas(month)       # queimadas set–nov
        elif cidade == "Salvador":
            pm25_base = 13.0
            fator = _sazonalidade_inverno(month, 0.20)
        elif cidade == "Recife":
            pm25_base = 12.0
            fator = _sazonalidade_inverno(month, 0.18)
        elif cidade == "Fortaleza":
            pm25_base = 11.0
            fator = _sazonalidade_inverno(month, 0.15)
        else:  # Brasília
            pm25_base = 18.0
            # Brasília: seco de maio a setembro
            fator = 1.0 + 0.40 * np.exp(-((month - 7) ** 2) / 5.0)

        pm25 = max(1.0, pm25_base * fator * np.random.lognormal(0.0, 0.22))

        # ------------------------------------------------------------------
        # Demais poluentes
        # ------------------------------------------------------------------
        # PM10 proporcional ao PM2.5 com variação
        pm10 = pm25 * np.random.uniform(1.6, 2.1)

        # NO2: maior em SP e RJ (frota / indústria)
        no2_base = 45.0 if cidade in ("São Paulo", "Rio de Janeiro") else 25.0
        no2 = max(2.0, no2_base * _sazonalidade_inverno(month, 0.25) * np.random.lognormal(0.0, 0.30))

        # CO: unidade ppm
        co_base = 2.0 if cidade in ("São Paulo", "Rio de Janeiro") else 0.9
        co = max(0.1, co_base * _sazonalidade_inverno(month, 0.20) * np.random.lognormal(0.0, 0.28))

        # O3: pico no outono/primavera (mais radiação + precursores)
        o3_fator = 1.15 if month in (3, 4, 9, 10) else 0.90
        o3 = max(5.0, np.random.normal(60.0, 15.0) * o3_fator)

        # ------------------------------------------------------------------
        # Temperatura (°C)  — variação regional coerente
        # ------------------------------------------------------------------
        if cidade in ("Manaus",):
            # Equatorial: quente e úmido o ano todo, pequena variação
            temp = np.random.normal(27.5, 1.5) + 1.5 * np.cos((month - 7) * 2 * np.pi / 12)
        elif cidade in ("Fortaleza", "Recife", "Salvador"):
            # Litoral NE/BA: quente com mínima sazonalidade
            temp = np.random.normal(27.0, 1.8) + 2.0 * np.cos((month - 7) * 2 * np.pi / 12)
        elif cidade in ("Curitiba", "Porto Alegre"):
            # Sul: estações bem marcadas
            temp = 20.0 - 10.0 * np.cos((month - 1) * 2 * np.pi / 12) + np.random.normal(0, 2.5)
        elif cidade == "Brasília":
            # Cerrado: calor com chuvas no verão, seco e ameno no inverno
            temp = 23.0 - 4.0 * np.cos((month - 1) * 2 * np.pi / 12) + np.random.normal(0, 2.0)
        else:
            # SP, RJ, BH: subtropical com estações moderadas
            temp = 23.0 - 6.0 * np.cos((month - 1) * 2 * np.pi / 12) + np.random.normal(0, 2.0)

        # ------------------------------------------------------------------
        # Umidade (%)
        # ------------------------------------------------------------------
        if cidade == "Manaus":
            umidade = np.clip(np.random.normal(85.0, 7.0) - 12 * np.sin((month - 3) * np.pi / 6), 55, 100)
        elif cidade in ("Fortaleza", "Recife", "Salvador"):
            umidade = np.clip(np.random.normal(75.0, 8.0), 40, 98)
        elif cidade in ("Curitiba", "Porto Alegre"):
            umidade = np.clip(np.random.normal(72.0, 10.0) + 8 * np.cos((month - 7) * 2 * np.pi / 12), 35, 98)
        elif cidade == "Brasília":
            # Muito seco no inverno
            umidade = np.clip(70.0 - 30.0 * np.cos((month - 1) * 2 * np.pi / 12) + np.random.normal(0, 8), 10, 98)
        else:
            umidade = np.clip(np.random.normal(68.0, 10.0) + 8 * np.cos((month - 7) * 2 * np.pi / 12), 30, 98)

        rows.append(
            {
                "data": date,
                "cidade": cidade,
                "estado": estado,
                "latitude": lat,
                "longitude": lon,
                "pm25": round(float(pm25), 2),
                "pm10": round(float(pm10), 2),
                "no2": round(float(no2), 2),
                "co": round(float(co), 3),
                "o3": round(float(o3), 2),
                "temperatura": round(float(temp), 1),
                "umidade": round(float(umidade), 1),
                "iqa": _iqa_de_pm25(float(pm25)),
            }
        )

df = pd.DataFrame(rows)

output_path = Path(__file__).parent / "ar_brasil.parquet"
df.to_parquet(output_path, index=False)

print(f"Total de registros : {len(df):,}")
print(f"Período            : {df['data'].min().date()} → {df['data'].max().date()}")
print(f"Cidades            : {', '.join(sorted(df['cidade'].unique()))}")
print(f"Arquivo gerado     : {output_path}")

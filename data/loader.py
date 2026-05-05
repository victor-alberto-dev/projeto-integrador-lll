
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

_PARQUET = Path(__file__).parent / "ar_brasil.parquet"
_GENERATOR = Path(__file__).parent / "generate_data.py"


@st.cache_data
def carregar_dados() -> pd.DataFrame:
    """Lê data/ar_brasil.parquet e retorna o DataFrame.

    Se o arquivo não existir, executa generate_data.py automaticamente
    antes de carregar.
    """
    if not _PARQUET.exists():
        subprocess.run([sys.executable, str(_GENERATOR)], check=True)

    df = pd.read_parquet(_PARQUET)
    df["data"] = pd.to_datetime(df["data"])
    return df

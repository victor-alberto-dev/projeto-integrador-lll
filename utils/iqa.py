# Cálculo do Índice de Qualidade do Ar (IQA) conforme padrões CONAMA

from __future__ import annotations

# Faixas: (limite_inferior, limite_superior, categoria, cor_hex, indice_min, indice_max)
_FAIXAS: dict[str, list[tuple]] = {
    "pm25": [
        (0, 25, "Bom", "#00E400", 0, 50),
        (25, 50, "Moderado", "#FFFF00", 51, 100),
        (50, 75, "Ruim", "#FF7E00", 101, 150),
        (75, 125, "Muito Ruim", "#FF0000", 151, 200),
        (125, float("inf"), "Péssimo", "#8F3F97", 201, 500),
    ],
    "pm10": [
        (0, 50, "Bom", "#00E400", 0, 50),
        (50, 100, "Moderado", "#FFFF00", 51, 100),
        (100, 150, "Ruim", "#FF7E00", 101, 150),
        (150, 250, "Muito Ruim", "#FF0000", 151, 200),
        (250, float("inf"), "Péssimo", "#8F3F97", 201, 500),
    ],
    "no2": [
        (0, 100, "Bom", "#00E400", 0, 50),
        (100, 200, "Moderado", "#FFFF00", 51, 100),
        (200, 360, "Ruim", "#FF7E00", 101, 150),
        (360, 600, "Muito Ruim", "#FF0000", 151, 200),
        (600, float("inf"), "Péssimo", "#8F3F97", 201, 500),
    ],
    "co": [
        (0, 9, "Bom", "#00E400", 0, 50),
        (9, 15, "Moderado", "#FFFF00", 51, 100),
        (15, 30, "Ruim", "#FF7E00", 101, 150),
        (30, 40, "Muito Ruim", "#FF0000", 151, 200),
        (40, float("inf"), "Péssimo", "#8F3F97", 201, 500),
    ],
    "o3": [
        (0, 100, "Bom", "#00E400", 0, 50),
        (100, 130, "Moderado", "#FFFF00", 51, 100),
        (130, 200, "Ruim", "#FF7E00", 101, 150),
        (200, 400, "Muito Ruim", "#FF0000", 151, 200),
        (400, float("inf"), "Péssimo", "#8F3F97", 201, 500),
    ],
}

_ALIAS: dict[str, str] = {
    "pm2.5": "pm25",
    "pm25": "pm25",
    "pm10": "pm10",
    "no2": "no2",
    "co": "co",
    "o3": "o3",
}

ORDEM_CATEGORIAS = ["Bom", "Moderado", "Ruim", "Muito Ruim", "Péssimo"]


def calcular_iqa(poluente: str, concentracao: float) -> dict:
    chave = _ALIAS.get(poluente.lower().strip())
    if chave is None:
        return {"categoria": "Desconhecido", "cor": "#AAAAAA", "indice": 0}

    for c_min, c_max, categoria, cor, i_min, i_max in _FAIXAS[chave]:
        if c_min <= concentracao < c_max:
            # Interpolação linear dentro da faixa
            if c_max == float("inf"):
                indice = i_max
            else:
                frac = (concentracao - c_min) / (c_max - c_min)
                indice = int(i_min + frac * (i_max - i_min))
            return {"categoria": categoria, "cor": cor, "indice": max(0, min(500, indice))}

    # Caso concentração seja negativa ou zero
    return {"categoria": "Bom", "cor": "#00E400", "indice": 0}


def cor_categoria(categoria: str) -> str:
    """Retorna a cor hex associada a uma categoria IQA."""
    mapa = {
        "Bom": "#00E400",
        "Moderado": "#FFFF00",
        "Ruim": "#FF7E00",
        "Muito Ruim": "#FF0000",
        "Péssimo": "#8F3F97",
        "Desconhecido": "#AAAAAA",
    }
    return mapa.get(categoria, "#AAAAAA")

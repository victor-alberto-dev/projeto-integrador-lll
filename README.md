# Qualidade do Ar — Brasil

Dashboard interativo de monitoramento de qualidade do ar para as dez maiores cidades brasileiras, construído com Streamlit e Plotly. Funciona completamente offline — sem API key, sem dependências externas.

---

## Visão geral

| Item | Detalhe |
|---|---|
| Período dos dados | Janeiro 2025 até a data atual |
| Cidades | São Paulo, Rio de Janeiro, Belo Horizonte, Curitiba, Porto Alegre, Salvador, Recife, Manaus, Fortaleza, Brasília |
| Granularidade | Diária |
| Poluentes | PM2.5, PM10, NO2, CO, O3 |
| Índice de qualidade | IQA calculado conforme faixas CONAMA a partir do PM2.5 |

---

## Estrutura do projeto

```
projeto-ar/
├── app.py                  # Aplicação Streamlit principal
├── requirements.txt        # Dependências Python
├── data/
│   ├── __init__.py
│   ├── generate_data.py    # Gerador de dados simulados → ar_brasil.parquet
│   ├── loader.py           # Função carregar_dados() com cache
│   ├── openaq_client.py    # Lista de cidades (integração API removida)
│   └── ar_brasil.parquet   # Dados gerados (ignorado pelo git se configurado)
└── utils/
    ├── __init__.py
    └── iqa.py              # Cálculo e faixas do IQA conforme CONAMA
```

---

## Instalação e execução

### 1. Clone o repositório e crie o ambiente virtual

```bash
git clone <url-do-repositorio>
cd projeto-ar
python -m venv .venv
```

### 2. Ative o ambiente virtual

**Windows (PowerShell)**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Gere os dados simulados

```bash
python data/generate_data.py
```

Saída esperada:
```
Total de registros : 4.870
Período            : 2025-01-01 → 2026-05-02
Cidades            : Belo Horizonte, Brasília, Curitiba, ...
Arquivo gerado     : data/ar_brasil.parquet
```

> O arquivo é gerado automaticamente na primeira execução do app, caso não exista.

### 5. Execute o dashboard

```bash
streamlit run app.py
```

Acesse em `http://localhost:8501`.

---

## Dependências

```
streamlit>=1.32
pandas>=2.0
numpy>=1.26
plotly>=5.18
pyarrow>=14.0
```

---

## Lógica de simulação

Os dados são gerados em `data/generate_data.py` com as seguintes regras:

- **Sazonalidade**: poluição 30–50 % maior no inverno (jun–ago) para cidades do Sul e Sudeste, simulando inversão térmica
- **Queimadas**: Manaus recebe pico de PM2.5 (até 80+ µg/m³) entre setembro e novembro
- **Frota e indústria**: São Paulo e Rio de Janeiro têm níveis cronicamente mais altos de PM2.5 e NO2
- **Temperatura e umidade**: variação regional coerente — equatorial (Manaus), semiárido (Fortaleza/Recife), subtropical (Curitiba/Porto Alegre), cerrado (Brasília)
- **Ruído**: distribuição lognormal via NumPy para evitar curvas perfeitas

---

## Substituindo por dados reais

1. Gere ou obtenha um arquivo com as colunas abaixo no formato Parquet:

   `data`, `cidade`, `estado`, `latitude`, `longitude`, `pm25`, `pm10`, `no2`, `co`, `o3`, `temperatura`, `umidade`, `iqa`

2. Salve como `data/ar_brasil.parquet`

3. Execute `streamlit run app.py` — nenhuma outra alteração é necessária

---

## Abas do dashboard

| Aba | Conteúdo |
|---|---|
| Visão Geral | KPIs, mapa interativo por cidade, evolução diária do IQA |
| Poluentes | Concentração média por cidade (barras), heatmap mensal, dispersão temporal |
| Estações | Tabela resumo por cidade, série temporal com todos os poluentes |
| Dados Brutos | Tabela filtrável com exportação CSV |

---

## Faixas IQA — CONAMA

| Categoria | PM2.5 (µg/m³) | Cor |
|---|---|---|
| Bom | 0 – 25 | Verde |
| Moderado | 25 – 50 | Amarelo |
| Ruim | 50 – 75 | Laranja |
| Muito Ruim | 75 – 125 | Vermelho |
| Péssimo | > 125 | Roxo |

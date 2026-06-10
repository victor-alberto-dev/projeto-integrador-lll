# Qualidade do Ar — Brasil

Dashboard interativo de monitoramento de qualidade do ar para as dez maiores cidades brasileiras, construído com Streamlit e Plotly. Os dados são carregados via **Open-Meteo API gratuita**, sem necessidade de registro.

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
│   ├── loader.py           # Função carregar_dados() via Open-Meteo API
│   ├── openaq_client.py    # Lista de cidades e coordenadas
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

### 4. Execute o dashboard

```bash
streamlit run app.py
```

Acesse em `http://localhost:8501`.

---

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
requests>=2.31
```

---

## Dados reais via Open-Meteo

O app carrega os dados diretamente da Open-Meteo API para as cidades listadas no diretório `data/`. Não é necessário gerar ou armazenar um arquivo local.

---

O app não requer arquivo local para dados: ele carrega as leituras diretamente da Open-Meteo API para as cidades monitoradas.

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

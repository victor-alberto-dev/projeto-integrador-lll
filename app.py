
"""
Dashboard de Qualidade do Ar — Grandes Cidades Brasileiras
Fonte de dados: simulada 
"""

from __future__ import annotations

import sys
import os

# Garante que os módulos locais sejam encontrados
sys.path.insert(0, os.path.dirname(__file__))

import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Tema padrão para todos os gráficos Plotly
px.defaults.template = "plotly_white"

from data.loader import carregar_dados
from data.openaq_client import CIDADES_ALVO
from utils.iqa import ORDEM_CATEGORIAS, calcular_iqa, cor_categoria

# Configuração da página

st.set_page_config(
    layout="wide",
    page_title="Qualidade do Ar — Brasil",
)

st.markdown("""
<style>
/* oculta itens desnecessarios do Streamlit */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }

/* container principal com mais respiro */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1440px;
}

/* metric cards: fundo branco, borda cinza clara */
[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1rem 1.25rem !important;
}
[data-testid="stMetricLabel"] > div {
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #64748b !important;
}
[data-testid="stMetricValue"] > div {
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    color: #1e293b !important;
}
</style>
""", unsafe_allow_html=True)

# Sidebar

with st.sidebar:
    st.markdown("## Qualidade do Ar")
    st.markdown("Dados simulados com padrões realistas de **poluição brasileira**")
    st.divider()

    cidade_opcoes = ["Todas"] + sorted(CIDADES_ALVO)
    cidade_sel = st.selectbox("Cidade", cidade_opcoes, index=0)

    # Dados cobrem jan/2025 até a data atual
    _hoje = datetime.date.today()
    periodo = st.date_input(
        "Período de análise",
        value=(datetime.date(2025, 1, 1), _hoje),
        min_value=datetime.date(2025, 1, 1),
        max_value=_hoje,
    )
    if isinstance(periodo, (list, tuple)) and len(periodo) == 2:
        data_inicio, data_fim = periodo
    else:
        data_inicio = datetime.date(2025, 1, 1)
        data_fim = _hoje

    poluentes_opcoes = ["PM2.5", "PM10", "NO2", "CO", "O3"]
    poluentes_sel = st.multiselect(
        "Poluentes",
        poluentes_opcoes,
        default=["PM2.5", "PM10"],
    )

    if st.button("Atualizar dados"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.caption(f"Período disponível: jan/2025 – {datetime.date.today().strftime('%d/%m/%Y')}")

# Mapeamento poluente label → coluna no parquet

POLUENTE_MAP: dict[str, str] = {
    "PM2.5": "pm25",
    "PM10":  "pm10",
    "NO2":   "no2",
    "CO":    "co",
    "O3":    "o3",
}

# Carregamento e filtragem de dados

with st.spinner("Carregando dados..."):
    df_full = carregar_dados()

# Filtro de período
ts_inicio = pd.Timestamp(data_inicio)
ts_fim = pd.Timestamp(data_fim)
df = df_full[(df_full["data"] >= ts_inicio) & (df_full["data"] <= ts_fim)].copy()

# Filtro de cidade
if cidade_sel != "Todas":
    df = df[df["cidade"] == cidade_sel]

if df.empty:
    st.warning("Nenhum dado encontrado para a cidade/período selecionado.")
    st.stop()

# Construir df_estacoes — snapshot da última data disponível por cidade
# (uma "estação" por cidade)

df_estacoes = (
    df.sort_values("data")
    .groupby("cidade")
    .last()
    .reset_index()
)
df_estacoes["nome"] = df_estacoes["cidade"]
df_estacoes["ultima_leitura"] = df_estacoes["data"].dt.strftime("%Y-%m-%d")

# Calcula IQA a partir do PM2.5 da última leitura
_iqa_calc = df_estacoes["pm25"].apply(lambda v: calcular_iqa("pm25", v))
df_estacoes["iqa_categoria"] = _iqa_calc.apply(lambda x: x["categoria"])
df_estacoes["iqa_cor"]       = _iqa_calc.apply(lambda x: x["cor"])
df_estacoes["iqa_indice"]    = _iqa_calc.apply(lambda x: x["indice"])


# Construir df_serie — dados diários "long" para os poluentes selecionados
pol_colunas = [POLUENTE_MAP[p] for p in poluentes_sel if p in POLUENTE_MAP]

if pol_colunas:
    df_serie = df[["data", "cidade", "estado", "latitude", "longitude"] + pol_colunas].melt(
        id_vars=["data", "cidade", "estado", "latitude", "longitude"],
        value_vars=pol_colunas,
        var_name="pol_chave",
        value_name="value",
    )
    # Mapeia de volta para label de exibição (ex.: "pm25" → "PM2.5")
    _chave_para_label = {v: k for k, v in POLUENTE_MAP.items()}
    df_serie["poluente_label"] = df_serie["pol_chave"].map(_chave_para_label)
    df_serie["datetime_local"] = pd.to_datetime(df_serie["data"])
else:
    df_serie = pd.DataFrame()

date_from_str = data_inicio.strftime("%Y-%m-%d")
date_to_str = data_fim.strftime("%Y-%m-%d")

# Abas principais

tab1, tab2, tab3, tab4 = st.tabs(
    ["Visão Geral", "Poluentes", "Estações", "Dados Brutos"]
)

# ABA 1 — Visão Geral

with tab1:
    st.header("Visão Geral da Qualidade do Ar")

    # KPI Cards
    iqa_medio = df_estacoes["iqa_indice"].mean()
    iqa_medio_cat = calcular_iqa("pm25", 0)  # fallback
    if not df_estacoes.empty and df_estacoes["pm25"].notna().any():
        pm25_medio = df_estacoes["pm25"].mean()
        iqa_medio_cat = calcular_iqa("pm25", pm25_medio)

    cidade_mais_poluida = (
        df.groupby("cidade")["pm25"].mean().idxmax()
        if not df.empty
        else "—"
    )

    pol_critico = "—"
    if not df_serie.empty and "poluente_label" in df_serie.columns:
        media_pol = df_serie.groupby("poluente_label")["value"].mean()
        if not media_pol.empty:
            pol_critico = media_pol.idxmax()

    n_ativas = len(df_estacoes)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("IQA Médio Geral", f"{iqa_medio:.0f}", delta=iqa_medio_cat["categoria"])
    with k2:
        st.metric("Cidade Mais Poluída", cidade_mais_poluida)
    with k3:
        st.metric("Poluente Mais Crítico", pol_critico)
    with k4:
        st.metric("Cidades Monitoradas", n_ativas)

    st.divider()

    # Mapa interativo
    col_mapa, col_linha = st.columns([3, 2])

    with col_mapa:
        st.subheader("Mapa por Cidade")
        df_mapa = df_estacoes.dropna(subset=["latitude", "longitude"]).copy()
        df_mapa["pm25_display"] = df_mapa["pm25"].fillna(0)
        df_mapa["tamanho"] = df_mapa["pm25_display"].apply(lambda x: max(5, min(30, x / 2)) if x else 8)
        df_mapa["tooltip"] = df_mapa.apply(
            lambda r: f"{r['nome']} | {r['cidade']} | IQA: {r['iqa_indice']:.0f} ({r['iqa_categoria']}) | PM2.5: {r['pm25_display']:.1f} µg/m³",
            axis=1,
        )

        if not df_mapa.empty:
            fig_mapa = px.scatter_mapbox(
                df_mapa,
                lat="latitude",
                lon="longitude",
                color="iqa_categoria",
                size="tamanho",
                hover_name="nome",
                hover_data={"cidade": True, "iqa_indice": True, "pm25_display": True, "tamanho": False},
                color_discrete_map={
                    "Bom": "#00E400",
                    "Moderado": "#FFFF00",
                    "Ruim": "#FF7E00",
                    "Muito Ruim": "#FF0000",
                    "Péssimo": "#8F3F97",
                    "Desconhecido": "#AAAAAA",
                },
                mapbox_style="open-street-map",
                zoom=3.5,
                center={"lat": -14.0, "lon": -51.0},
                height=450,
                labels={
                    "iqa_categoria": "Categoria IQA",
                    "iqa_indice": "IQA",
                    "pm25_display": "PM2.5 (µg/m³)",
                    "cidade": "Cidade",
                },
            )
            fig_mapa.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
            st.plotly_chart(fig_mapa, use_container_width=True)
        else:
            st.warning("Sem coordenadas disponíveis para exibir o mapa.")

    with col_linha:
        st.subheader("Evolução Diária do IQA por Cidade")
        if not df_serie.empty and "datetime_local" in df_serie.columns:
            df_iqa_dia = df_serie.dropna(subset=["value", "datetime_local"]).copy()
            df_iqa_dia["data"] = pd.to_datetime(df_iqa_dia["datetime_local"]).dt.date

            iqa_rows = []
            for _, r in df_iqa_dia.iterrows():
                pol = r.get("pol_chave", r.get("poluente_label", "pm25"))
                res = calcular_iqa(str(pol), float(r["value"]))
                iqa_rows.append(res["indice"])
            df_iqa_dia["iqa_val"] = iqa_rows

            df_evolucao = (
                df_iqa_dia.groupby(["data", "cidade"])["iqa_val"]
                .mean()
                .reset_index()
            )
            fig_linha = px.line(
                df_evolucao,
                x="data",
                y="iqa_val",
                color="cidade",
                labels={"data": "Data", "iqa_val": "IQA Médio", "cidade": "Cidade"},
                height=450,
            )
            fig_linha.update_layout(legend_title_text="Cidade")
            st.plotly_chart(fig_linha, use_container_width=True)
        else:
            st.info("Selecione ao menos um poluente para exibir a evolução diária do IQA.")

# ABA 2 — Poluentes

with tab2:
    st.header("Análise por Poluente")

    if not poluentes_sel:
        st.warning("Selecione ao menos um poluente na barra lateral.")
    else:
        pol_ativo = st.selectbox("Poluente para análise", poluentes_sel, key="pol_tab2")
        pol_chave = POLUENTE_MAP[pol_ativo]

        # Concentração média por cidade (barras horizontais)
        st.subheader(f"Concentração Média de {pol_ativo} por Cidade")
        df_pol_cidade = (
            df.groupby("cidade")[pol_chave]
            .mean()
            .reset_index()
            .rename(columns={pol_chave: "value"})
            .sort_values("value", ascending=True)
        )

        if df_pol_cidade.empty:
            st.warning(f"Sem dados de {pol_ativo} para o período selecionado.")
        else:
            df_pol_cidade["categoria"] = df_pol_cidade["value"].apply(
                lambda v: calcular_iqa(pol_chave, v)["categoria"]
            )
            df_pol_cidade["cor"] = df_pol_cidade["categoria"].apply(cor_categoria)

            limite_bom = {
                "pm25": 25, "pm10": 50, "no2": 100, "co": 9, "o3": 100
            }.get(pol_chave, None)

            fig_barras = go.Figure()
            fig_barras.add_trace(
                go.Bar(
                    x=df_pol_cidade["value"],
                    y=df_pol_cidade["cidade"],
                    orientation="h",
                    marker_color=df_pol_cidade["cor"].tolist(),
                    text=df_pol_cidade["value"].round(1),
                    textposition="outside",
                    name=pol_ativo,
                )
            )
            if limite_bom:
                fig_barras.add_vline(
                    x=limite_bom,
                    line_dash="dash",
                    line_color="green",
                    annotation_text=f"Limite Bom ({limite_bom})",
                    annotation_position="top right",
                )
            fig_barras.update_layout(
                xaxis_title=f"Concentração de {pol_ativo}",
                yaxis_title="Cidade",
                height=400,
                showlegend=False,
            )
            st.plotly_chart(fig_barras, use_container_width=True)

        st.subheader(f"Média Mensal de {pol_ativo} por Cidade")

        df_mensal = df.copy()
        df_mensal["mes"] = df_mensal["data"].dt.month
        df_mensal_agg = (
            df_mensal.groupby(["cidade", "mes"])[pol_chave]
            .mean()
            .reset_index()
            .rename(columns={pol_chave: "value"})
        )

        if df_mensal_agg.empty:
            st.info("Sem dados mensais disponíveis para este poluente.")
        else:
            _MESES = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
                      7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}
            df_mensal_agg["mes_label"] = df_mensal_agg["mes"].map(_MESES)
            pivot = df_mensal_agg.pivot_table(
                index="cidade", columns="mes_label", values="value"
            )
            # Reordena colunas por mês
            meses_presentes = [_MESES[m] for m in sorted(_MESES) if _MESES[m] in pivot.columns]
            pivot = pivot[meses_presentes]

            fig_heat = px.imshow(
                pivot,
                labels={"x": "Mês", "y": "Cidade", "color": f"{pol_ativo}"},
                color_continuous_scale="RdYlGn_r",
                aspect="auto",
                height=350,
            )
            fig_heat.update_layout(xaxis_title="Mês", yaxis_title="Cidade")
            st.plotly_chart(fig_heat, use_container_width=True)

        # Dispersão: data × concentração por cidade
        st.subheader(f"Dispersão: Concentração de {pol_ativo} por Cidade")
        if not df_serie.empty:
            df_disp = df_serie[df_serie["poluente_label"] == pol_ativo].dropna(subset=["value"])
            if df_disp.empty:
                st.info("Sem dados suficientes para o gráfico de dispersão.")
            else:
                df_disp = df_disp.copy()
                df_disp["data_plot"] = pd.to_datetime(df_disp["datetime_local"], errors="coerce").dt.date
                fig_disp = px.scatter(
                    df_disp,
                    x="data_plot",
                    y="value",
                    color="cidade",
                    labels={"data_plot": "Data", "value": f"Concentração {pol_ativo}", "cidade": "Cidade"},
                    height=350,
                    opacity=0.7,
                )
                st.plotly_chart(fig_disp, use_container_width=True)

# ABA 3 — Estações

with tab3:
    st.header("Estações de Monitoramento")

    # Tabela resumo (uma linha por cidade)
    df_tabela = df_estacoes[["nome", "cidade", "iqa_categoria", "iqa_indice", "ultima_leitura"]].copy()
    df_tabela.columns = ["Nome", "Cidade", "Categoria IQA", "Índice IQA", "Última Leitura"]
    df_tabela["Status"] = df_tabela["Índice IQA"].apply(lambda x: "Ativo" if x > 0 else "Inativo")
    st.dataframe(df_tabela, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Série Temporal por Cidade")

    estacoes_lista = df_estacoes["nome"].tolist()
    if estacoes_lista:
        estacao_sel = st.selectbox("Selecione uma estação", estacoes_lista, key="est_tab3")

        # Série diária de todos os poluentes para a cidade selecionada
        df_est_cidade = df[df["cidade"] == estacao_sel].copy()
        _todos_pol = ["pm25", "pm10", "no2", "co", "o3"]
        _label_map = {v: k for k, v in POLUENTE_MAP.items()}

        df_est_serie = df_est_cidade[["data"] + _todos_pol].melt(
            id_vars=["data"],
            value_vars=_todos_pol,
            var_name="pol_chave",
            value_name="value",
        )
        df_est_serie["poluente"] = df_est_serie["pol_chave"].map(_label_map)

        if not df_est_serie.empty:
            fig_est = px.line(
                df_est_serie,
                x="data",
                y="value",
                color="poluente",
                labels={"data": "Data", "value": "Concentração", "poluente": "Poluente"},
                title=f"Série Temporal — {estacao_sel}",
                height=400,
            )
            st.plotly_chart(fig_est, use_container_width=True)
        else:
            st.warning("Sem dados disponíveis para esta estação no período selecionado.")

# ABA 4 — Dados Brutos

with tab4:
    st.header("Dados Brutos")

    # Exibe o DataFrame no formato wide (uma linha por cidade × dia).
    # Cada cidade tem latitude/longitude únicos — sem repetição de valores
    # causada pelo formato long/melted usado nos gráficos.
    _colunas_raw = ["data", "cidade", "estado", "pm25", "pm10", "no2", "co", "o3",
                    "temperatura", "umidade", "iqa"]
    df_raw_base = df[_colunas_raw].copy()

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        cidades_disp = ["Todas"] + sorted(df_raw_base["cidade"].dropna().unique().tolist())
        cidade_filtro = st.selectbox("Filtrar por cidade", cidades_disp, key="cidade_raw")
    with col_f2:
        st.markdown("&nbsp;", unsafe_allow_html=True)  # alinha com o selectbox ao lado

    df_raw = df_raw_base.copy()
    if cidade_filtro != "Todas":
        df_raw = df_raw[df_raw["cidade"] == cidade_filtro]

    df_raw = df_raw.rename(columns={
        "data": "Data", "cidade": "Cidade", "estado": "Estado",
        "pm25": "PM2.5 (µg/m³)", "pm10": "PM10 (µg/m³)",
        "no2": "NO2 (µg/m³)", "co": "CO (ppm)", "o3": "O3 (µg/m³)",
        "temperatura": "Temp. (°C)", "umidade": "Umidade (%)", "iqa": "IQA",
    })

    st.dataframe(df_raw, use_container_width=True, hide_index=True)
    st.caption(f"Total de registros: {len(df_raw):,}")

    csv = df_raw.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Exportar CSV",
        data=csv,
        file_name=f"qualidade_ar_{date_from_str}_{date_to_str}.csv",
        mime="text/csv",
    )


"""Dashboard Streamlit que consome o relatório já processado em data/output."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
RELATORIO = ROOT / "data" / "output" / "relatorio_conferencia_lotes.xlsx"
CLASSIFICACOES = ("Válido", "Divergência", "Ambíguo", "Erro de Entrada")
COLUNA_CLASSIFICACAO = "Classificação"
COLUNA_DATA_REFERENCIA = "Data de referência"
PALETA_CARMESIM = ["#5C0011", "#8A1024", "#B71C35", "#D94B62"]

st.set_page_config(page_title="Conferência de Lotes", page_icon="📊", layout="wide")
st.title("Conferência de Lotes")

if not RELATORIO.exists():
    st.error("Relatório ainda não encontrado. Execute `python dashboard/gerar_relatorio.py` primeiro.")
    st.stop()


@st.cache_data
def carregar_relatorio(caminho: str) -> pd.DataFrame:
    return pd.read_excel(caminho, sheet_name="Todos")


todos = carregar_relatorio(str(RELATORIO))
totais = todos[COLUNA_CLASSIFICACAO].value_counts().reindex(CLASSIFICACOES, fill_value=0)
colunas = st.columns(4)
for coluna, classificacao in zip(colunas, CLASSIFICACOES):
    quantidade = int(totais[classificacao])
    coluna.metric(classificacao, quantidade)

esquerda, direita = st.columns(2)
with esquerda:
    st.subheader("Classificações")
    distribuicao = totais.rename_axis(COLUNA_CLASSIFICACAO).reset_index(name="quantidade")
    grafico_rosquinha = px.pie(
        distribuicao,
        values="quantidade",
        names=COLUNA_CLASSIFICACAO,
        hole=0.55,
        color_discrete_sequence=PALETA_CARMESIM,
    )
    grafico_rosquinha.update_traces(textinfo="percent+label", textposition="inside")
    grafico_rosquinha.update_layout(showlegend=False, margin={"t": 0, "b": 0, "l": 0, "r": 0})
    st.plotly_chart(grafico_rosquinha, width="stretch")
with direita:
    st.subheader("Alertas por dia (Divergências + Ambíguos)")
    alertas = (todos.assign(alerta=todos[COLUNA_CLASSIFICACAO].isin(["Divergência", "Ambíguo"]).astype(int))
        .groupby(COLUNA_DATA_REFERENCIA, sort=False)["alerta"].sum())
    st.line_chart(alertas, color="#B71C35")

st.subheader("Registros processados")
filtro = st.multiselect("Classificação", CLASSIFICACOES, default=list(CLASSIFICACOES))
st.dataframe(todos.loc[todos[COLUNA_CLASSIFICACAO].isin(filtro)], width="stretch", hide_index=True)
with RELATORIO.open("rb") as arquivo:
    st.download_button("Baixar relatório Excel", arquivo.read(), file_name=RELATORIO.name)

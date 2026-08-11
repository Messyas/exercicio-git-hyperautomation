"""Dashboard Streamlit que consome o relatório já processado em data/output."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
RELATORIO = ROOT / "data" / "output" / "relatorio_conferencia_lotes.xlsx"
CLASSIFICACOES = ("Válido", "Divergência", "Ambíguo", "Erro de Entrada")

st.set_page_config(page_title="Conferência de Lotes", page_icon="📊", layout="wide")
st.title("Conferência de Lotes — PIM")
st.caption("Dashboard baseado no relatório processado em data/output.")

if not RELATORIO.exists():
    st.error("Relatório ainda não encontrado. Execute `python dashboard/gerar_relatorio.py` primeiro.")
    st.stop()


@st.cache_data
def carregar_relatorio(caminho: str) -> pd.DataFrame:
    return pd.read_excel(caminho, sheet_name="Todos")


todos = carregar_relatorio(str(RELATORIO))
totais = todos["classificacao"].value_counts().reindex(CLASSIFICACOES, fill_value=0)
colunas = st.columns(4)
for coluna, classificacao in zip(colunas, CLASSIFICACOES):
    quantidade = int(totais[classificacao])
    coluna.metric(classificacao, quantidade, f"{quantidade / len(todos):.1%}")

esquerda, direita = st.columns(2)
with esquerda:
    st.subheader("Classificações")
    distribuicao = totais.rename_axis("classificacao").reset_index(name="quantidade")
    st.vega_lite_chart(
        distribuicao,
        {
            "mark": {"type": "arc", "tooltip": True},
            "encoding": {
                "theta": {"field": "quantidade", "type": "quantitative"},
                "color": {"field": "classificacao", "type": "nominal"},
                "tooltip": [
                    {"field": "classificacao", "type": "nominal", "title": "Classificacao"},
                    {"field": "quantidade", "type": "quantitative", "title": "Quantidade"},
                ],
            },
        },
        use_container_width=True,
    )
with direita:
    st.subheader("Alertas por dia (Divergências + Ambíguos)")
    alertas = (todos.assign(alerta=todos["classificacao"].isin(["Divergência", "Ambíguo"]).astype(int))
        .groupby("data_referencia", sort=False)["alerta"].sum())
    st.line_chart(alertas)

st.subheader("Registros processados")
filtro = st.multiselect("Classificação", CLASSIFICACOES, default=list(CLASSIFICACOES))
st.dataframe(todos.loc[todos["classificacao"].isin(filtro)], use_container_width=True, hide_index=True)
with RELATORIO.open("rb") as arquivo:
    st.download_button("Baixar relatório Excel", arquivo.read(), file_name=RELATORIO.name)

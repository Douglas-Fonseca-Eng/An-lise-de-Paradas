import streamlit as st

from src.analytics import picos_temporais, serie_temporal
from src.charts import grafico_serie_temporal
from src.dashboard import cabecalho, obter_dados, obter_dados_filtrados
from src.utils import formatar_decimal, formatar_inteiro

FREQUENCIAS = {"Dia": "D", "Semana": "W"}

df = obter_dados_filtrados()

cabecalho(
    "Análise temporal",
    "Como a quantidade de paradas e o tempo parado evoluem ao longo do período.",
)

if obter_dados().empty:
    st.warning("Nenhum dado no banco ainda. Importe uma planilha para começar.")
    st.stop()

if df.empty:
    st.info("Nenhuma parada corresponde aos filtros selecionados.")
    st.stop()

coluna_a, coluna_b = st.columns(2)
granularidade = coluna_a.radio("Agrupar por", list(FREQUENCIAS), horizontal=True)
separacao = coluna_b.radio("Separar por", ["Total", "CT"], horizontal=True)

serie = serie_temporal(df, FREQUENCIAS[granularidade], "ct" if separacao == "CT" else None)

st.subheader(f"Quantas paradas ocorreram por {granularidade.lower()}?")
st.plotly_chart(grafico_serie_temporal(serie, "paradas", "Paradas"))

st.subheader(f"Quantas horas ficaram paradas por {granularidade.lower()}?")
st.plotly_chart(grafico_serie_temporal(serie, "horas", "Horas paradas"))

picos = picos_temporais(serie)
prefixo = "Dia" if granularidade == "Dia" else "Semana iniciada em"
st.caption(
    f"Pico de paradas: {prefixo.lower()} {picos['periodo_paradas']:%d/%m/%Y} "
    f"({formatar_inteiro(picos['max_paradas'])} paradas). "
    f"Pico de tempo parado: {prefixo.lower()} {picos['periodo_horas']:%d/%m/%Y} "
    f"({formatar_decimal(picos['max_horas'])} h)."
)
st.caption(
    "O tempo de cada parada é contado inteiro no período em que ela começou. "
    "Uma parada longa, que atravessa vários dias, aparece toda no dia em que começou."
)
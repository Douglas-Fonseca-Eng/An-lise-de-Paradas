import streamlit as st

from src.analytics import (horas_de_turno_no_periodo, janela_de_analise,
                           resumo_por_grupo, resumo_turnos, serie_temporal)
from src.charts import grafico_ranking, grafico_serie_temporal, grafico_turnos
from src.components import mostrar_kpis
from src.dashboard import cabecalho, obter_dados, obter_dados_filtrados, obter_periodo_filtrado

TOP_N = 8

# texto da medida -> (coluna do resumo por grupo, coluna do resumo de turnos, coluna da série temporal, rótulo)
MEDIDAS = {
    "Paradas": ("paradas", "paradas", "paradas", "Paradas"),
    "Horas paradas": ("tempo_horas", "tempo_horas", "horas", "Horas paradas"),
}

df = obter_dados_filtrados()

cabecalho("Máquinas", "Visão detalhada de cada máquina (CT).")

if obter_dados().empty:
    st.warning("Nenhum dado no banco ainda. Importe uma planilha para começar.")
    st.stop()

if df.empty:
    st.info("Nenhuma parada corresponde aos filtros selecionados.")
    st.stop()

coluna_a, coluna_b = st.columns(2)
maquina = coluna_a.selectbox("CT", sorted(df["ct"].unique()))
medida = coluna_b.radio("Medida dos gráficos", list(MEDIDAS), horizontal=True)
col_grupo, col_turno, col_serie, rotulo = MEDIDAS[medida]

df_maquina = df[df["ct"] == maquina]

st.subheader(f"Indicadores de {maquina}")
mostrar_kpis(df_maquina)

esquerda, direita = st.columns(2)

with esquerda:
    st.subheader("Quais motivos mais pesam?")
    motivos = resumo_por_grupo(df_maquina, "motivo").sort_values(col_grupo, ascending=False).head(TOP_N)
    st.plotly_chart(grafico_ranking(motivos, col_grupo, rotulo))
    st.caption(f"Os {len(motivos)} principais motivos. Ausentes aparecem como Não informado.")

with direita:
    st.subheader("Quais origens mais pesam?")
    origens = resumo_por_grupo(df_maquina, "origem").sort_values(col_grupo, ascending=False).head(TOP_N)
    st.plotly_chart(grafico_ranking(origens, col_grupo, rotulo))
    st.caption("Ausentes aparecem como Não informado.")

esquerda, direita = st.columns(2)

with esquerda:
    st.subheader("Como se distribui entre os turnos?")
    inicio, fim = janela_de_analise(obter_dados(), obter_periodo_filtrado())
    turnos = resumo_turnos(df_maquina, horas_de_turno_no_periodo(inicio, fim))
    st.plotly_chart(grafico_turnos(turnos, col_turno, rotulo))

with direita:
    st.subheader("Como evolui ao longo dos dias?")
    serie = serie_temporal(df_maquina, "D")
    st.plotly_chart(grafico_serie_temporal(serie, col_serie, rotulo))
    st.caption("O tempo de cada parada é contado inteiro no dia em que ela começou.")
import streamlit as st

from src.analytics import destaque_participacao, resumo_por_grupo
from src.charts import grafico_participacao
from src.dashboard import cabecalho, obter_dados, obter_dados_filtrados

DIMENSOES = {
    "Máquina (CT)": "ct",
    "Turno": "turno",
    "Origem": "origem",
    "Faixa de duração": "faixa_duracao",
}

df = obter_dados_filtrados()

cabecalho(
    "Quantidade x indisponibilidade",
    "Quem para mais vezes nem sempre é quem fica mais tempo parado.",
)

if obter_dados().empty:
    st.warning("Nenhum dado no banco ainda. Importe uma planilha para começar.")
    st.stop()

if df.empty:
    st.info("Nenhuma parada corresponde aos filtros selecionados.")
    st.stop()

escolha = st.radio("Comparar por", list(DIMENSOES), horizontal=True)
resumo = resumo_por_grupo(df, DIMENSOES[escolha])

st.subheader("Quem concentra mais paradas também concentra mais tempo parado?")
st.plotly_chart(grafico_participacao(resumo, escolha))
st.caption(destaque_participacao(resumo))

st.subheader("Números por grupo")
tabela = resumo[["grupo", "paradas", "pct_paradas", "tempo_horas", "pct_tempo", "media_min", "mediana_min"]]
tabela = tabela.rename(columns={
    "grupo": escolha,
    "paradas": "Paradas",
    "pct_paradas": "% das paradas",
    "tempo_horas": "Tempo parado (h)",
    "pct_tempo": "% do tempo",
    "media_min": "Média (min)",
    "mediana_min": "Mediana (min)",
}).round(1)
st.dataframe(tabela, hide_index=True)
st.caption("Tempo parado é a soma das durações de todas as paradas do grupo.")
import streamlit as st

from src.analytics import janela_de_analise, matriz_calor
from src.charts import grafico_mapa_calor
from src.dashboard import cabecalho, obter_dados, obter_dados_filtrados, obter_periodo_filtrado
from src.utils import formatar_decimal

# texto da medida -> (coluna, rótulo, casas decimais)
MEDIDAS = {
    "Paradas": ("paradas", "Paradas", 0),
    "Horas paradas": ("tempo_horas", "Horas paradas", 1),
}

df = obter_dados_filtrados()

cabecalho("Mapa de calor", "Em quais dias da semana e horários as paradas se concentram.")

if obter_dados().empty:
    st.warning("Nenhum dado no banco ainda. Importe uma planilha para começar.")
    st.stop()

if df.empty:
    st.info("Nenhuma parada corresponde aos filtros selecionados.")
    st.stop()

coluna_a, coluna_b = st.columns(2)
nome_medida = coluna_a.radio("Medida", list(MEDIDAS), horizontal=True)
normalizar = coluna_b.checkbox(
    "Média por ocorrência",
    help=(
        "Divide cada célula pelo número de vezes que aquele dia da semana e aquela hora "
        "aconteceram no período. Corrige o fato de alguns dias aparecerem mais vezes "
        "(por exemplo, um mês pode ter 5 terças e só 4 segundas)."
    ),
)

coluna, rotulo, casas = MEDIDAS[nome_medida]
inicio, fim = janela_de_analise(obter_dados(), obter_periodo_filtrado())
matriz = matriz_calor(df, coluna, inicio, fim, normalizar)

if normalizar:
    rotulo = f"{rotulo} (média por ocorrência)"
    casas = 1

st.subheader("Em quais dias e horas as paradas se concentram?")
st.plotly_chart(grafico_mapa_calor(matriz, rotulo, casas))

valores = matriz.stack()
dia, hora = valores.idxmax()
st.caption(f"Maior valor: {dia}, às {hora:02d}h ({formatar_decimal(valores.max(), casas)}).")
st.caption(
    "Cada parada é contada na hora em que começou. No caso de Horas paradas, "
    "o tempo inteiro da parada vai para a hora do início."
)
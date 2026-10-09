import streamlit as st

from src.analytics import categorias_ate_percentual, pareto
from src.charts import grafico_pareto
from src.dashboard import cabecalho, obter_dados, obter_dados_filtrados
from src.filters import ROTULO_NAO_INFORMADO
from src.utils import formatar_decimal

# texto da dimensão -> (coluna, plural para o título)
DIMENSOES = {
    "Motivo": ("motivo", "motivos"),
    "Origem": ("origem", "origens"),
    "Tag": ("tag", "tags"),
}

# texto da medida -> (coluna, rótulo do eixo, casas decimais, "de que" nas frases, rótulo do percentual)
MEDIDAS = {
    "Paradas": ("paradas", "Paradas", 0, "das paradas", "% das paradas"),
    "Horas paradas": ("tempo_horas", "Horas paradas", 1, "do tempo parado", "% do tempo"),
}

df = obter_dados_filtrados()

cabecalho("Pareto", "Quais causas concentram a maior parte das paradas ou do tempo parado.")

if obter_dados().empty:
    st.warning("Nenhum dado no banco ainda. Importe uma planilha para começar.")
    st.stop()

if df.empty:
    st.info("Nenhuma parada corresponde aos filtros selecionados.")
    st.stop()

coluna_a, coluna_b, coluna_c = st.columns(3)
nome_dimensao = coluna_a.radio("Analisar por", list(DIMENSOES), horizontal=True)
nome_medida = coluna_b.radio("Medida", list(MEDIDAS), horizontal=True)
quantos = coluna_c.slider("Mostrar os maiores", min_value=5, max_value=30, value=10)
ocultar = st.checkbox(
    f"Ocultar {ROTULO_NAO_INFORMADO}",
    help="Mostra o Pareto só das paradas que têm essa informação preenchida.",
)

coluna_dimensao, plural = DIMENSOES[nome_dimensao]
coluna_medida, rotulo, casas, de_que, rotulo_pct = MEDIDAS[nome_medida]
resumo = pareto(df, coluna_dimensao, coluna_medida, ocultar)

if resumo.empty:
    st.info("Não há categorias para mostrar com esta seleção.")
    st.stop()

st.subheader(f"Quais {plural} concentram a maior parte {de_que}?")
st.plotly_chart(grafico_pareto(resumo.head(quantos), rotulo, casas))

ate_80 = categorias_ate_percentual(resumo, 80)
st.caption(f"{ate_80} de {len(resumo)} categorias respondem por pelo menos 80% {de_que}.")

nao_informado = resumo[resumo["grupo"] == ROTULO_NAO_INFORMADO]
if not nao_informado.empty:
    st.caption(
        f"{ROTULO_NAO_INFORMADO}: {formatar_decimal(nao_informado['pct'].iloc[0])}% {de_que}. "
        "Marque a caixa acima para ver o Pareto só das categorias informadas."
    )

st.subheader("Números completos")
tabela = resumo[["posicao", "grupo", "paradas", "tempo_horas", "pct", "pct_acumulado"]].rename(columns={
    "posicao": "Posição",
    "grupo": nome_dimensao,
    "paradas": "Paradas",
    "tempo_horas": "Tempo parado (h)",
    "pct": rotulo_pct,
    "pct_acumulado": "% acumulado",
}).round(1)
st.dataframe(tabela, hide_index=True)
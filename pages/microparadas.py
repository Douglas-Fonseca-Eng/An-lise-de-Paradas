import streamlit as st

from config.settings import LIMITE_MICROPARADA_MIN
from src.analytics import detectar_rajadas, intervalos_entre_microparadas, resumo_janelas, serie_horaria
from src.charts import grafico_serie_temporal
from src.components import cartao
from src.dashboard import cabecalho, obter_dados, obter_dados_filtrados
from src.utils import formatar_inteiro, formatar_minutos, formatar_percentual, rotulo_limite

JANELAS = [10, 20, 30, 40, 60, 120]
LINHAS_RAJADAS = 20

df = obter_dados_filtrados()

cabecalho(
    "Microparadas",
    f"Paradas de até {rotulo_limite(LIMITE_MICROPARADA_MIN)}: frequência, intervalos e rajadas.",
)

if obter_dados().empty:
    st.warning("Nenhum dado no banco ainda. Importe uma planilha para começar.")
    st.stop()

if df.empty:
    st.info("Nenhuma parada corresponde aos filtros selecionados.")
    st.stop()

micro = df[df["microparada"]]
if micro.empty:
    st.info("Não há microparadas nas paradas selecionadas.")
    st.stop()

st.subheader("Definição de rajada")
coluna_a, coluna_b = st.columns(2)
lacuna = coluna_a.slider("Intervalo máximo entre microparadas da mesma rajada (min)", 1, 60, 10)
minimo = coluna_b.slider("Mínimo de microparadas para formar uma rajada", 2, 20, 5)
st.caption(
    "Uma rajada é uma sequência de microparadas da mesma CT em que cada uma começa, no máximo, "
    f"{lacuna} min depois do fim da anterior. Só aparecem as rajadas com {minimo} microparadas ou mais."
)

rajadas = detectar_rajadas(micro, lacuna, minimo)
intervalos = intervalos_entre_microparadas(micro)

cartoes = st.columns(5)
cartao(cartoes[0], "Microparadas", formatar_inteiro(len(micro)), f"{formatar_percentual(len(micro), len(df))} das paradas")
cartao(cartoes[1], "Duração mediana", formatar_minutos(micro["duracao_minutos"].median()), f"até {rotulo_limite(LIMITE_MICROPARADA_MIN)}")
cartao(cartoes[2], "Intervalo mediano", formatar_minutos(intervalos.median()), "entre microparadas da mesma CT")
cartao(cartoes[3], "Rajadas", formatar_inteiro(len(rajadas)), f"{minimo}+ microparadas, intervalo até {lacuna} min")
em_rajadas = int(rajadas["microparadas"].sum())
cartao(cartoes[4], "Microparadas em rajadas", formatar_inteiro(em_rajadas), f"{formatar_percentual(em_rajadas, len(micro))} das microparadas")

st.subheader("Como as microparadas se acumulam ao longo do dia?")
por_dia = micro.groupby(micro["data_inicio"].dt.date).size()
dias = sorted(por_dia.index)
dia = st.selectbox(
    "Dia", dias, index=dias.index(por_dia.idxmax()), format_func=lambda d: d.strftime("%d/%m/%Y"),
)
serie = serie_horaria(micro, dia)
st.plotly_chart(
    grafico_serie_temporal(serie, "paradas", "Microparadas", formato_eixo="%Hh", formato_hover="%d/%m %Hh")
)
st.caption(
    "Cada ponto é uma hora do dia, uma linha por CT. O dia que abre selecionado é o de mais microparadas "
    f"({formatar_inteiro(por_dia.max())})."
)

st.subheader("Quantas microparadas aconteceram nos minutos anteriores?")
janelas = resumo_janelas(micro, JANELAS, minimo)
tabela_janelas = janelas.rename(columns={
    "janela_min": "Janela (min)",
    "media": "Média",
    "p90": "90% têm até",
    "maximo": "Máximo",
    "pct_minimo": f"% com {minimo} ou mais",
}).round(1)
st.dataframe(tabela_janelas, hide_index=True)
st.caption(
    "Para cada microparada, conta quantas outras microparadas da mesma CT aconteceram nos N minutos "
    "anteriores. É a leitura histórica do que, mais adiante, poderá alimentar os modelos preditivos."
)

st.subheader(f"As {LINHAS_RAJADAS} maiores rajadas")
if rajadas.empty:
    st.info("Nenhuma rajada com esta definição. Reduza o mínimo ou aumente o intervalo máximo.")
else:
    tabela_rajadas = rajadas.head(LINHAS_RAJADAS).copy()
    tabela_rajadas["inicio"] = tabela_rajadas["inicio"].dt.strftime("%d/%m/%Y %H:%M")
    tabela_rajadas["fim"] = tabela_rajadas["fim"].dt.strftime("%d/%m/%Y %H:%M")
    tabela_rajadas = tabela_rajadas.rename(columns={
        "ct": "CT", "inicio": "Início", "fim": "Fim",
        "microparadas": "Microparadas", "duracao_min": "Duração da rajada (min)",
    }).round(1)
    st.dataframe(tabela_rajadas, hide_index=True)
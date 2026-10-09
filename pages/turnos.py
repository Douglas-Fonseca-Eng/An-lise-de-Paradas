import streamlit as st

from config.settings import LIMITE_MICROPARADA_MIN, LIMITES_PARADA_LONGA_MIN
from src.analytics import horas_de_turno_no_periodo, janela_de_analise, resumo_turnos
from src.charts import grafico_turnos
from src.dashboard import cabecalho, obter_dados, obter_dados_filtrados, obter_periodo_filtrado
from src.utils import formatar_decimal, rotulo_limite

# texto da medida -> (coluna do resumo, rótulo do eixo, pergunta)
MEDIDAS = {
    "Paradas": ("paradas", "Paradas", "Qual turno tem mais paradas?"),
    "Horas paradas": ("tempo_horas", "Horas paradas", "Qual turno acumula mais tempo parado?"),
    "Paradas por hora de turno": (
        "paradas_por_hora", "Paradas por hora de turno",
        "Qual turno para com mais frequência, descontando o tamanho do turno?",
    ),
}

df = obter_dados_filtrados()

cabecalho("Turnos", "Comparação entre os turnos, inclusive por máquina.")

if obter_dados().empty:
    st.warning("Nenhum dado no banco ainda. Importe uma planilha para começar.")
    st.stop()

if df.empty:
    st.info("Nenhuma parada corresponde aos filtros selecionados.")
    st.stop()

inicio, fim = janela_de_analise(obter_dados(), obter_periodo_filtrado())
horas_turno = horas_de_turno_no_periodo(inicio, fim)

coluna_a, coluna_b = st.columns(2)
medida = coluna_a.radio("Medida", list(MEDIDAS), horizontal=True)
separacao = coluna_b.radio("Separar por", ["Total", "CT"], horizontal=True)

resumo = resumo_turnos(df, horas_turno, separar_por_ct=(separacao == "CT"))
coluna, rotulo, pergunta = MEDIDAS[medida]

st.subheader(pergunta)
st.plotly_chart(grafico_turnos(resumo, coluna, rotulo))

horas_texto = "; ".join(f"{turno} {formatar_decimal(h)} h" for turno, h in horas_turno.items())
st.caption(
    "Os turnos têm durações diferentes, então comparar só a quantidade favorece injustamente "
    "o turno mais longo. Paradas por hora de turno divide as paradas pelas horas do turno "
    f"existentes no período. Horas de turno no período: {horas_texto}."
)

st.subheader("Números por turno")
colunas = ["turno"] + (["grupo"] if separacao == "CT" else []) + [
    "paradas", "tempo_horas", "media_min", "mediana_min", "microparadas",
] + [f"acima_{limite}" for limite in LIMITES_PARADA_LONGA_MIN] + ["paradas_por_hora"]

nomes = {
    "turno": "Turno",
    "grupo": "CT",
    "paradas": "Paradas",
    "tempo_horas": "Tempo parado (h)",
    "media_min": "Média (min)",
    "mediana_min": "Mediana (min)",
    "microparadas": f"Microparadas (até {rotulo_limite(LIMITE_MICROPARADA_MIN)})",
    "paradas_por_hora": "Paradas por hora de turno",
}
nomes.update({f"acima_{limite}": f"Acima de {rotulo_limite(limite)}" for limite in LIMITES_PARADA_LONGA_MIN})

tabela = resumo[colunas].rename(columns=nomes).round(
    {"Tempo parado (h)": 1, "Média (min)": 1, "Mediana (min)": 1, "Paradas por hora de turno": 2}
)
st.dataframe(tabela, hide_index=True)
import streamlit as st

from src.dashboard import barra_lateral

st.set_page_config(page_title="Análise de Paradas", layout="wide")

navegacao = st.navigation(
    [
        st.Page("pages/visao_geral.py", title="Visão geral", default=True),
        st.Page("pages/quantidade_x_tempo.py", title="Quantidade x indisponibilidade"),
        st.Page("pages/analise_temporal.py", title="Análise temporal"),
        st.Page("pages/turnos.py", title="Turnos"),
        st.Page("pages/maquinas.py", title="Máquinas"),
        st.Page("pages/pareto.py", title="Pareto"),
        st.Page("pages/mapa_calor.py", title="Mapa de calor"),
        st.Page("pages/microparadas.py", title="Microparadas"),
        st.Page("pages/eventos.py", title="Eventos"),
        st.Page("pages/qualidade_dados.py", title="Qualidade dos dados"),
        st.Page("pages/importacao.py", title="Importação"),
    ]
)
barra_lateral()
navegacao.run()
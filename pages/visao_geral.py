import streamlit as st

from src.components import mostrar_kpis
from src.dashboard import cabecalho, obter_dados, obter_dados_filtrados, obter_motor
from src.importer import listar_arquivos_importados

df = obter_dados_filtrados()

cabecalho("Visão geral", "Sistema de apoio à decisão. Apenas análise: não controla equipamentos.")

if obter_dados().empty:
    st.warning("Nenhum dado no banco ainda. Importe uma planilha para começar.")
    st.stop()

if df.empty:
    st.info("Nenhuma parada corresponde aos filtros selecionados.")
    st.stop()

mostrar_kpis(df, ver_paradas=True)

with st.expander("Arquivos importados"):
    st.dataframe(listar_arquivos_importados(obter_motor()), hide_index=True)
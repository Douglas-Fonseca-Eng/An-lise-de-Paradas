"""
Peças compartilhadas por todas as páginas do dashboard.
"""
import streamlit as st

from src.analytics import carregar_paradas, obter_versao_dados
from src.database import criar_tabelas, obter_engine
from src.filters import (FILTROS_ADICIONAIS, FILTROS_PRINCIPAIS, OPCOES_QUEBRA,
                         aplicar_filtros, opcoes_da_coluna, periodo_apos_nova_importacao)
from src.importer import listar_arquivos_importados
from src.utils import formatar_inteiro, resumo_dados


@st.cache_resource
def obter_motor():
    """Cria a conexão com o banco uma única vez e a reaproveita em todas as interações."""
    motor = obter_engine()
    criar_tabelas(motor)
    return motor


@st.cache_data(max_entries=2)
def _carregar(versao_dados):
    """Lê as paradas do banco. O cache é renovado quando a versão dos dados muda."""
    return carregar_paradas(obter_motor())


def obter_dados():
    """Devolve o DataFrame de paradas (do cache; renovado a cada nova importação)."""
    return _carregar(obter_versao_dados(obter_motor()))


def obter_dados_filtrados():
    """Devolve as paradas já filtradas pelos filtros globais da barra lateral."""
    if "dados_filtrados" in st.session_state:
        return st.session_state["dados_filtrados"]
    return obter_dados()


def obter_periodo_filtrado():
    """Período (data inicial, data final) escolhido no filtro, ou None se não houver restrição."""
    return st.session_state.get("periodo_filtrado")


def cabecalho(titulo, subtitulo=None):
    """Cabeçalho padrão de todas as páginas."""
    st.title(titulo)
    if subtitulo:
        st.caption(subtitulo)


def _limpar_filtros(data_min, data_max):
    """Volta todos os filtros para o estado inicial."""
    st.session_state["filtro_periodo"] = (data_min, data_max)
    for coluna, _ in FILTROS_PRINCIPAIS + FILTROS_ADICIONAIS:
        st.session_state[f"filtro_{coluna}"] = []
    st.session_state["filtro_quebra"] = OPCOES_QUEBRA[0]


def _painel_filtros(df):
    """Desenha os filtros na barra lateral e devolve o DataFrame já filtrado."""
    data_min = df["data_inicio"].min().date()
    data_max = df["data_inicio"].max().date()

    # Se o usuário estava vendo o período completo e a base cresceu (nova importação),
    # o período acompanha o novo intervalo. Se ele escolheu um período próprio, é mantido.
    intervalo_atual = (data_min, data_max)
    selecionado = st.session_state.get("filtro_periodo")
    if selecionado is not None:
        st.session_state["filtro_periodo"] = periodo_apos_nova_importacao(
            selecionado, st.session_state.get("intervalo_dados"), intervalo_atual,
        )
    st.session_state["intervalo_dados"] = intervalo_atual

    st.subheader("Filtros")
    periodo = st.date_input(
        "Período", value=(data_min, data_max), min_value=data_min, max_value=data_max,
        format="DD/MM/YYYY", key="filtro_periodo",
    )

    escolhas = {}
    for coluna, rotulo in FILTROS_PRINCIPAIS:
        escolhas[coluna] = st.multiselect(
            rotulo, opcoes_da_coluna(df, coluna), key=f"filtro_{coluna}", placeholder="Todas",
        )

    with st.expander("Mais filtros"):
        for coluna, rotulo in FILTROS_ADICIONAIS:
            escolhas[coluna] = st.multiselect(
                rotulo, opcoes_da_coluna(df, coluna), key=f"filtro_{coluna}", placeholder="Todos",
            )
        quebra = st.selectbox("Quebra", OPCOES_QUEBRA, key="filtro_quebra")

    st.button("Limpar filtros", on_click=_limpar_filtros, args=(data_min, data_max))

    periodo_completo = isinstance(periodo, (tuple, list)) and len(periodo) == 2
    if not periodo_completo:
        st.caption("Escolha também a data final do período.")

    filtros = {
        "periodo": tuple(periodo) if periodo_completo and tuple(periodo) != (data_min, data_max) else None,
        "categoricos": escolhas,
        "quebra": quebra,
    }
    df_filtrado = aplicar_filtros(df, filtros)
    st.session_state["periodo_filtrado"] = filtros["periodo"]
    st.caption(f"{formatar_inteiro(len(df_filtrado))} de {formatar_inteiro(len(df))} paradas selecionadas")
    return df_filtrado


def barra_lateral():
    """Barra lateral fixa (filtros e estado dos dados). Aparece em todas as páginas."""
    df = obter_dados()
    historico = listar_arquivos_importados(obter_motor())

    with st.sidebar:
        df_filtrado = df if df.empty else _painel_filtros(df)
        st.divider()
        st.subheader("Dados")
        for linha in resumo_dados(df, historico):
            st.caption(linha)
        if st.button("Recarregar dados"):
            st.cache_data.clear()
            st.rerun()

    st.session_state["dados_filtrados"] = df_filtrado
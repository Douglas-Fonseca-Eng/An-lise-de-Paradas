"""
Blocos visuais reutilizados em mais de uma página.
"""
import streamlit as st

from config.settings import LIMITE_MICROPARADA_MIN, LIMITES_PARADA_LONGA_MIN
from src.analytics import calcular_kpis
from src.utils import (formatar_horas, formatar_inteiro, formatar_minutos,
                       formatar_percentual, rotulo_limite)


def cartao(coluna, rotulo, valor, detalhe=None, recorte=None):
    """
    Um indicador dentro de um cartão com borda.
    Se 'recorte' for informado, o cartão ganha um botão que abre a página Eventos já filtrada.
    """
    with coluna.container(border=True):
        st.metric(rotulo, valor)
        if detalhe:
            st.caption(detalhe)
        if recorte and st.button("Ver paradas", key=f"ver_{recorte}"):
            st.session_state["recorte_inicial"] = recorte
            st.switch_page("pages/eventos.py")


def mostrar_kpis(df, ver_paradas=False):
    """
    Mostra as duas linhas de indicadores (cartões) para as paradas recebidas.
    Com ver_paradas=True, os cartões de quantidade têm o botão que leva à página Eventos.
    """
    kpis = calcular_kpis(df)
    total = kpis["total_paradas"]

    linha1 = st.columns(4)
    cartao(
        linha1[0], "Total de paradas", formatar_inteiro(total), f"em {kpis['maquinas']} máquina(s)",
        recorte="Todas as paradas" if ver_paradas else None,
    )
    cartao(linha1[1], "Tempo total parado", formatar_horas(kpis["tempo_total_min"]), "soma de todas as máquinas")
    cartao(linha1[2], "Duração média", formatar_minutos(kpis["media_min"]))
    cartao(linha1[3], "Duração mediana", formatar_minutos(kpis["mediana_min"]), "metade das paradas dura menos que isso")

    linha2 = st.columns(2 + len(LIMITES_PARADA_LONGA_MIN))
    cartao(linha2[0], "Maior parada", formatar_minutos(kpis["maior_min"]))
    cartao(
        linha2[1], "Microparadas", formatar_inteiro(kpis["microparadas"]),
        f"até {rotulo_limite(LIMITE_MICROPARADA_MIN)} · {formatar_percentual(kpis['microparadas'], total)} das paradas",
        recorte="Microparadas" if ver_paradas else None,
    )
    for coluna, limite in zip(linha2[2:], LIMITES_PARADA_LONGA_MIN):
        quantidade = kpis["acima_de"][limite]
        cartao(
            coluna, f"Acima de {rotulo_limite(limite)}", formatar_inteiro(quantidade),
            f"{formatar_percentual(quantidade, total)} das paradas",
            recorte=f"Acima de {rotulo_limite(limite)}" if ver_paradas else None,
        )

    if kpis["em_andamento"]:
        st.caption(
            f"{kpis['em_andamento']} parada(s) ainda em andamento na exportação: "
            "a duração delas é provisória e já entra nos totais acima."
        )
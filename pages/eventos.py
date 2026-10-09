import streamlit as st

from src.dashboard import cabecalho, obter_dados, obter_dados_filtrados
from src.filters import aplicar_recorte, buscar_texto, opcoes_recorte
from src.utils import detalhes_da_parada, formatar_inteiro

COLUNAS_TABELA = [
    "data_inicio", "data_fim", "ct", "turno", "duracao_minutos", "motivo", "origem", "tag", "operador",
]
NOMES_TABELA = {
    "data_inicio": "Data início",
    "data_fim": "Data fim",
    "ct": "CT",
    "turno": "Turno",
    "duracao_minutos": "Duração (min)",
    "motivo": "Motivo",
    "origem": "Origem",
    "tag": "Tag",
    "operador": "Operador",
}

df = obter_dados_filtrados()

cabecalho("Eventos", "Cada parada individual, com busca, ordenação e detalhes.")

if obter_dados().empty:
    st.warning("Nenhum dado no banco ainda. Importe uma planilha para começar.")
    st.stop()

if df.empty:
    st.info("Nenhuma parada corresponde aos filtros selecionados.")
    st.stop()

# Vindo de um cartão da Visão geral: abre já no recorte do indicador clicado.
recorte_inicial = st.session_state.pop("recorte_inicial", None)
if recorte_inicial in opcoes_recorte():
    st.session_state["recorte_eventos"] = recorte_inicial

coluna_a, coluna_b, coluna_c = st.columns([2, 2, 3])
recorte = coluna_a.selectbox("Mostrar", opcoes_recorte(), key="recorte_eventos")
ordem = coluna_b.radio("Ordenar por", ["Mais recentes", "Maior duração"], horizontal=True)
texto = coluna_c.text_input("Buscar", placeholder="Motivo, tag, operador, providência...")

filtrado = buscar_texto(aplicar_recorte(df, recorte), texto)
if ordem == "Mais recentes":
    filtrado = filtrado.sort_values("data_inicio", ascending=False)
else:
    filtrado = filtrado.sort_values("duracao_minutos", ascending=False)
filtrado = filtrado.reset_index(drop=True)

if filtrado.empty:
    st.info("Nenhuma parada encontrada com esta seleção.")
    st.stop()

tabela = filtrado[COLUNAS_TABELA].rename(columns=NOMES_TABELA)
for coluna in ["Motivo", "Origem", "Tag", "Operador"]:
    tabela[coluna] = tabela[coluna].astype("object").where(tabela[coluna].notna(), "—")

st.caption(
    f"{formatar_inteiro(len(filtrado))} paradas ({formatar_inteiro(len(df))} nos filtros da barra lateral). "
    "Clique no número à esquerda de uma linha para ver os detalhes."
)

selecao = st.dataframe(
    tabela,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    key="tabela_eventos",
    column_config={
        "Data início": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm:ss"),
        "Data fim": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm:ss"),
        "Duração (min)": st.column_config.NumberColumn(format="%.1f"),
    },
)

csv = tabela.round({"Duração (min)": 2}).to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
st.download_button("Baixar esta tabela (CSV)", csv, file_name="paradas.csv", mime="text/csv")

linhas = selecao.selection.rows
if linhas:
    parada = filtrado.iloc[linhas[0]]
    quando, o_que = detalhes_da_parada(parada)

    st.subheader(f"Detalhes da parada {parada['id_origem']}")
    esquerda, direita = st.columns(2)
    for coluna, titulo, itens in [(esquerda, "Quando", quando), (direita, "O que aconteceu", o_que)]:
        with coluna.container(border=True):
            st.markdown(f"**{titulo}**")
            for rotulo, valor in itens:
                st.markdown(f"{rotulo}: **{valor}**")
else:
    st.caption("Selecione uma linha da tabela para ver todos os detalhes da parada.")
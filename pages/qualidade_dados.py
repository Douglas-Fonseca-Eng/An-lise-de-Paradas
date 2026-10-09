import streamlit as st

from src.components import cartao
from src.dashboard import cabecalho, obter_dados, obter_motor
from src.importer import listar_arquivos_importados
from src.quality import (categorias_inconsistentes, colunas_totalmente_vazias,
                         tabela_ausentes, verificacoes)
from src.utils import formatar_inteiro

df = obter_dados()

cabecalho(
    "Qualidade dos dados",
    "Como estão os dados gravados no banco. Esta página usa todos os registros, sem os filtros da barra lateral.",
)

if df.empty:
    st.warning("Nenhum dado no banco ainda. Importe uma planilha para começar.")
    st.stop()

historico = listar_arquivos_importados(obter_motor())
checagens = verificacoes(df)
checagens["situacao"] = checagens["quantidade"].map(lambda n: "OK" if n == 0 else "Atenção")
vazias = colunas_totalmente_vazias(df)
com_atencao = int((checagens["quantidade"] > 0).sum())

cartoes = st.columns(4)
cartao(cartoes[0], "Registros", formatar_inteiro(len(df)))
cartao(cartoes[1], "Arquivos importados", formatar_inteiro(len(historico)))
cartao(cartoes[2], "Colunas totalmente vazias", formatar_inteiro(len(vazias)))
cartao(cartoes[3], "Verificações com atenção", f"{com_atencao} de {len(checagens)}")

st.subheader("Verificações de consistência")
tabela_checagens = checagens[["verificacao", "quantidade", "situacao", "observacao"]].rename(columns={
    "verificacao": "Verificação",
    "quantidade": "Quantidade",
    "situacao": "Situação",
    "observacao": "Observação",
})
st.dataframe(tabela_checagens, hide_index=True)
st.caption(
    "Registros inválidos e repetidos são barrados na importação, por isso não chegam ao banco. "
    "O resumo do que foi barrado em cada arquivo está no histórico, mais abaixo."
)

st.subheader("Valores ausentes por coluna")
ausentes = tabela_ausentes(df).rename(columns={
    "coluna": "Coluna", "ausentes": "Ausentes", "pct_ausentes": "% ausentes",
})
st.dataframe(
    ausentes,
    hide_index=True,
    column_config={
        "% ausentes": st.column_config.ProgressColumn("% ausentes", min_value=0, max_value=100, format="%.1f"),
    },
)
st.caption(
    "Colunas totalmente vazias: " + (", ".join(vazias) if vazias else "nenhuma") + ". "
    'O texto "-" da planilha original já é contado como ausente.'
)

st.subheader("Categorias com variações de escrita")
variacoes = categorias_inconsistentes(df)
if variacoes.empty:
    st.success("Nenhuma variação encontrada.")
else:
    st.dataframe(
        variacoes.rename(columns={"coluna": "Coluna", "variantes": "Variantes", "registros": "Registros"}),
        hide_index=True,
    )
st.caption(
    "Valores que só diferem em maiúsculas, acentos, espaços ou pontuação. "
    "Em campos de texto livre, como Providência, isso é esperado, mas atrapalha a contagem por categoria."
)

st.subheader("Histórico de importações")
st.dataframe(historico, hide_index=True)
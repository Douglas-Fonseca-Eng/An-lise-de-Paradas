import pandas as pd
import streamlit as st

from config.settings import PASTA_IMPORTADOS
from src.analytics import obter_versao_dados
from src.components import cartao
from src.dashboard import cabecalho, obter_motor
from src.importer import (buscar_arquivo_importado, calcular_hash_conteudo, importar_dataframe,
                          obter_ids_existentes)
from src.leitura import aba_sugerida, extensao_do_arquivo, ler_arquivo, listar_abas
from src.previa import SITUACOES, montar_previa, problemas_por_linha
from src.utils import formatar_decimal, formatar_inteiro, formatar_tamanho
from src.validacao import validar_arquivo

LINHAS_MAXIMAS = 500


@st.cache_data(show_spinner="Abrindo o arquivo...")
def abas_do_arquivo(conteudo):
    return listar_abas(conteudo)


@st.cache_data(show_spinner="Lendo o arquivo...")
def ler(nome, conteudo, aba):
    return ler_arquivo(nome, conteudo, aba)


@st.cache_data(show_spinner="Validando os dados...")
def validar(nome, conteudo, aba, _df):
    # O parâmetro _df (com sublinhado) não entra na chave do cache: ela usa só nome, conteúdo e aba.
    return validar_arquivo(_df)


@st.cache_data(show_spinner="Montando a prévia...")
def montar(nome, conteudo, aba, versao_dados, _df, _relatorio):
    # versao_dados só existe para renovar o cache quando o banco muda; os parâmetros com sublinhado ficam fora da chave.
    return montar_previa(_df, _relatorio, obter_ids_existentes(obter_motor()))


def baixar_csv(tabela, nome_arquivo):
    csv = tabela.to_csv(index=False, sep=";").encode("utf-8-sig")
    st.download_button("Baixar esta lista (CSV)", csv, file_name=nome_arquivo, mime="text/csv")


cabecalho("Importação", "Envie uma nova planilha de paradas (Excel ou CSV).")

# Resultado de uma importação feita logo antes: aparece uma única vez.
resultado = st.session_state.pop("resultado_importacao", None)
if resultado:
    if resultado["status"] == "importado":
        st.success(
            f"Importação concluída: {formatar_inteiro(resultado['novos'])} registros novos gravados "
            f"(arquivo nº {resultado['arquivo_id']}). Ignorados: {formatar_inteiro(resultado['ja_existentes'])} "
            f"já existentes e {formatar_inteiro(resultado['repetidos_no_arquivo'])} repetidos no arquivo. "
            f"Recusados: {formatar_inteiro(resultado['invalidos'])} inválidos."
        )
        if resultado.get("copia_salva") is False:
            st.warning("Os dados foram gravados, mas não foi possível guardar uma cópia do arquivo original.")
        st.page_link("pages/visao_geral.py", label="Ver o dashboard atualizado")
    else:
        st.info("Este arquivo já tinha sido importado. Nada foi gravado.")

arquivo = st.file_uploader(
    "Selecione o arquivo",
    type=["xlsx", "csv"],
    help="Aceita Excel (.xlsx) e CSV. Se o seu arquivo for .xls, salve-o antes como .xlsx.",
)

if arquivo is None:
    st.info("Selecione um arquivo para começar. Nada é gravado até você confirmar a importação.")
    st.stop()

conteudo = arquivo.getvalue()
hash_arquivo = calcular_hash_conteudo(conteudo)
extensao = extensao_do_arquivo(arquivo.name)

aba = None
try:
    if extensao == ".xlsx":
        abas = abas_do_arquivo(conteudo)
        aba = st.selectbox("Aba", abas, index=abas.index(aba_sugerida(abas)))
    df = ler(arquivo.name, conteudo, aba)
except Exception as erro:
    st.error(f"Não foi possível ler o arquivo ({type(erro).__name__}): {erro}")
    st.stop()

if df.empty:
    st.warning("O arquivo foi lido, mas não tem nenhuma linha de dados.")
    st.stop()

try:
    relatorio = validar(arquivo.name, conteudo, aba, df)
except Exception as erro:
    st.error(f"Não foi possível validar o arquivo ({type(erro).__name__}): {erro}")
    st.stop()

st.subheader(arquivo.name)
cartoes = st.columns(4)
cartao(cartoes[0], "Tipo", "Excel" if extensao == ".xlsx" else "CSV", f"aba {aba}" if aba else None)
cartao(cartoes[1], "Tamanho", formatar_tamanho(arquivo.size))
cartao(cartoes[2], "Linhas de dados", formatar_inteiro(len(df)))
cartao(cartoes[3], "Colunas", formatar_inteiro(df.shape[1]))

st.subheader("Colunas encontradas")
reconhecidas = relatorio["colunas"]["renomeadas"]
tabela_colunas = pd.DataFrame({
    "Coluna no arquivo": [str(nome) for nome in df.columns],
    "Reconhecida como": [reconhecidas.get(nome, "não reconhecida") for nome in df.columns],
    "Valores preenchidos": df.notna().sum().to_numpy(),
    "Tipo lido": [str(tipo) for tipo in df.dtypes],
})
st.dataframe(tabela_colunas, hide_index=True)
if relatorio["colunas"]["desconhecidas"]:
    st.caption("Colunas não reconhecidas (serão ignoradas): " + ", ".join(relatorio["colunas"]["desconhecidas"]) + ".")
if relatorio["colunas"]["opcionais_ausentes"]:
    st.caption("Colunas opcionais ausentes: " + ", ".join(relatorio["colunas"]["opcionais_ausentes"]) + ".")

st.subheader("Validação")

if relatorio["bloqueios"]:
    st.error("Este arquivo não pode ser importado:\n\n" + "\n".join(f"- {motivo}" for motivo in relatorio["bloqueios"]))
    st.stop()

if relatorio["linhas_invalidas"]:
    st.warning(
        f"{formatar_inteiro(relatorio['linhas_invalidas'])} registro(s) com problema serão recusados. "
        f"Os outros {formatar_inteiro(relatorio['validos'])} podem ser importados."
    )
else:
    st.success("Nenhum registro inválido encontrado.")

resumo = st.columns(4)
cartao(resumo[0], "Registros no arquivo", formatar_inteiro(relatorio["total"]))
cartao(resumo[1], "Válidos", formatar_inteiro(relatorio["validos"]))
cartao(resumo[2], "Inválidos", formatar_inteiro(relatorio["linhas_invalidas"]), "serão recusados")
cartao(resumo[3], "Repetidos no arquivo", formatar_inteiro(relatorio["linhas_repetidas"]), "serão ignorados")

if relatorio["linhas_invalidas"]:
    with st.expander("Registros inválidos", expanded=True):
        invalidos = relatorio["invalidos"].rename(columns={
            "linha": "Linha no arquivo", "id_origem": "ID", "problema": "Problema",
        })
        st.dataframe(invalidos.head(LINHAS_MAXIMAS), hide_index=True)
        if len(invalidos) > LINHAS_MAXIMAS:
            st.caption(f"Mostrando os {LINHAS_MAXIMAS} primeiros problemas de {formatar_inteiro(len(invalidos))}.")
        st.caption("A linha 1 do arquivo é o cabeçalho. Um registro pode ter mais de um problema.")
        baixar_csv(invalidos, "registros_invalidos.csv")

if relatorio["linhas_repetidas"]:
    with st.expander("IDs repetidos no arquivo"):
        repetidos = relatorio["repetidos"].rename(columns={"linha": "Linha no arquivo", "id_origem": "ID"})
        st.dataframe(repetidos.head(LINHAS_MAXIMAS), hide_index=True)
        st.caption("Vale a primeira ocorrência de cada ID. As seguintes são ignoradas.")

avisos = {nome: quantidade for nome, quantidade in relatorio["avisos"].items() if quantidade}
if avisos:
    st.subheader("Avisos")
    st.markdown("\n".join(f"- {nome}: **{formatar_inteiro(quantidade)}**" for nome, quantidade in avisos.items()))
    if relatorio["ct_desconhecidas"]:
        st.warning(
            "CTs fora da lista conhecida: " + ", ".join(relatorio["ct_desconhecidas"]) + ". "
            "Elas não são convertidas automaticamente em nenhuma máquina: seriam importadas com a marca "
            "de CT desconhecida. Se forem apelidos de uma máquina que você conhece, confirme antes de importar."
        )

st.subheader("Prévia da importação")

motor = obter_motor()
ja_importado = buscar_arquivo_importado(motor, hash_arquivo)
if ja_importado:
    st.info(
        "Este arquivo, com exatamente este conteúdo, já foi importado em "
        f"{ja_importado['data_importacao']:%d/%m/%Y %H:%M} "
        f"(arquivo nº {ja_importado['id']}: {ja_importado['nome_arquivo']}). Importá-lo de novo não grava nada."
    )

previa = montar(arquivo.name, conteudo, aba, obter_versao_dados(motor), df, relatorio)
contagens = previa["contagens"]
periodo = previa["periodo"]

cartoes_previa = st.columns(4)
cartao(cartoes_previa[0], "Serão importados", formatar_inteiro(contagens["Novo"]), "registros novos")
cartao(cartoes_previa[1], "Já existem no banco", formatar_inteiro(contagens["Já existe no banco"]), "serão ignorados")
cartao(cartoes_previa[2], "Tempo parado dos novos", f"{formatar_decimal(previa['horas_novas'])} h")
cartao(
    cartoes_previa[3], "Período dos novos",
    f"{periodo[0]:%d/%m} a {periodo[1]:%d/%m}" if periodo else "—",
    f"{periodo[1]:%Y}" if periodo else None,
)

if contagens["Novo"]:
    por_ct = previa["por_ct"].rename(columns={"ct": "CT", "paradas": "Paradas", "horas": "Horas paradas"}).round(1)
    st.dataframe(por_ct, hide_index=True)
else:
    st.caption("Nenhum registro novo: nada seria gravado.")

st.subheader("Registros do arquivo")
situacao = st.selectbox(
    "Mostrar", SITUACOES, format_func=lambda nome: f"{nome} ({formatar_inteiro(contagens[nome])})",
)
processado = previa["processado"]
parte = processado[processado["situacao"] == situacao]

if parte.empty:
    st.info("Nenhum registro nesta situação.")
else:
    tabela = parte[[
        "linha_arquivo", "id_origem", "ct", "data_inicio", "data_fim", "duracao_minutos", "motivo", "origem", "turno",
    ]].rename(columns={
        "linha_arquivo": "Linha no arquivo", "id_origem": "ID", "ct": "CT", "data_inicio": "Data início",
        "data_fim": "Data fim", "duracao_minutos": "Duração (min)", "motivo": "Motivo", "origem": "Origem",
        "turno": "Turno",
    })
    for coluna in ["Motivo", "Origem"]:
        tabela[coluna] = tabela[coluna].astype("object").where(tabela[coluna].notna(), "—")
    if situacao == "Inválido":
        tabela["Problema"] = parte["linha_arquivo"].map(problemas_por_linha(relatorio)).to_numpy()
    st.dataframe(
        tabela.head(LINHAS_MAXIMAS),
        hide_index=True,
        column_config={
            "Data início": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm:ss"),
            "Data fim": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm:ss"),
            "Duração (min)": st.column_config.NumberColumn(format="%.1f"),
        },
    )
    if len(tabela) > LINHAS_MAXIMAS:
        st.caption(f"Mostrando os {LINHAS_MAXIMAS} primeiros de {formatar_inteiro(len(tabela))} registros.")

st.subheader("Confirmar importação")
novos = contagens["Novo"]
if novos == 0:
    st.info("Não há registros novos neste arquivo, então não há nada para importar.")
else:
    ignorados = relatorio["total"] - novos
    st.write(
        f"Serão gravados **{formatar_inteiro(novos)}** registros novos. Os outros {formatar_inteiro(ignorados)} "
        "não serão gravados, e nada que já está no banco será alterado ou apagado."
    )
    confirmado = st.checkbox("Revisei a prévia e confirmo a importação", key=f"confirmo_{hash_arquivo}")
    if st.button(f"Importar {formatar_inteiro(novos)} registros novos", type="primary", disabled=not confirmado):
        try:
            with st.spinner("Importando..."):
                resultado = importar_dataframe(arquivo.name, conteudo, df, motor, pasta_copia=PASTA_IMPORTADOS)
        except Exception as erro:
            st.error(f"A importação falhou e nada foi gravado ({type(erro).__name__}): {erro}")
        else:
            st.session_state["resultado_importacao"] = resultado
            st.rerun()
"""
Leitura de arquivos enviados pelo usuário (Excel ou CSV), a partir do conteúdo em memória.
São funções sem Streamlit, para poderem ser testadas sozinhas.
"""
from io import BytesIO, StringIO
from pathlib import Path

import pandas as pd

ABA_PADRAO = "Paradas"
CODIFICACOES = ("utf-8-sig", "cp1252")
SEPARADORES = (";", ",", "\t", "|")
EXTENSOES_ACEITAS = (".xlsx", ".csv")


def extensao_do_arquivo(nome):
    """'Paradas.XLSX' -> '.xlsx'"""
    return Path(nome).suffix.lower()


def listar_abas(conteudo):
    """Nomes das abas de um arquivo Excel. Se o arquivo não for um Excel válido, avisa com clareza."""
    try:
        return pd.ExcelFile(BytesIO(conteudo)).sheet_names
    except Exception as erro:
        raise ValueError("O arquivo não parece ser uma planilha Excel (.xlsx) válida.") from erro


def aba_sugerida(abas):
    """Aba chamada 'Paradas' (sem diferenciar maiúsculas); se não houver, a primeira."""
    for aba in abas:
        if aba.strip().lower() == ABA_PADRAO.lower():
            return aba
    return abas[0]


def _tentar_ler_csv(texto, separador):
    """Lê o texto com um separador. Se não conseguir, devolve uma tabela vazia."""
    try:
        decimal = "," if separador == ";" else "."
        return pd.read_csv(StringIO(texto), sep=separador, decimal=decimal)
    except (pd.errors.ParserError, pd.errors.EmptyDataError, ValueError):
        return pd.DataFrame()


def ler_csv(conteudo):
    """
    Lê um CSV de qualquer um dos formatos comuns: codificação UTF-8 ou Windows (cp1252) e
    separador ponto e vírgula, vírgula, tabulação ou barra vertical. Escolhe o separador que
    resulta em mais colunas. Com ponto e vírgula, assume vírgula como separador decimal.
    """
    for codificacao in CODIFICACOES:
        try:
            texto = conteudo.decode(codificacao)
        except UnicodeDecodeError:
            continue
        tentativas = [_tentar_ler_csv(texto, separador) for separador in SEPARADORES]
        melhor = max(tentativas, key=lambda tabela: tabela.shape[1])
        if melhor.shape[1] < 2:
            raise ValueError("Não foi possível identificar as colunas do CSV (separador desconhecido).")
        return melhor
    raise ValueError("Não foi possível decodificar o CSV (codificação desconhecida).")


def ler_arquivo(nome, conteudo, aba=None):
    """Lê um arquivo .xlsx (na aba indicada) ou .csv e devolve o DataFrame."""
    extensao = extensao_do_arquivo(nome)
    if extensao == ".xlsx":
        return pd.read_excel(BytesIO(conteudo), sheet_name=aba if aba is not None else 0)
    if extensao == ".csv":
        return ler_csv(conteudo)
    raise ValueError(f"Tipo de arquivo não aceito: '{extensao}'. Use .xlsx ou .csv.")
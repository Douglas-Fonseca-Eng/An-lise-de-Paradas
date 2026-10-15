"""
Validação de um arquivo já lido, antes de qualquer gravação no banco.
Devolve um relatório com: bloqueios, reconhecimento das colunas, registros inválidos,
registros repetidos e avisos. São funções sem Streamlit, para poderem ser testadas sozinhas.
"""
import pandas as pd

from config.schema import COLUNAS, COLUNAS_COM_MARCADOR_VAZIO, MARCADORES_VAZIO
from src.transformer import _converter_datas, _converter_duracao, aplicar_etl, renomear_colunas

COLUNAS_PROBLEMAS = ["linha", "id_origem", "problema"]


def _nome_original(interno):
    """'data_inicio' -> 'Data Inicio'"""
    return next((c["original"] for c in COLUNAS if c["interno"] == interno), interno)


def _data_ilegivel(serie):
    """Valor presente, que não é o marcador '-', mas que não pôde ser lido como data."""
    marcador = serie.astype(str).str.strip().isin(MARCADORES_VAZIO)
    return serie.notna() & ~marcador & _converter_datas(serie).isna()


def _tabela_problemas(linhas):
    return pd.DataFrame(linhas, columns=COLUNAS_PROBLEMAS)


def validar_arquivo(df):
    """
    Valida a tabela lida do arquivo (com os nomes de coluna originais) e devolve um dicionário:
      bloqueios  -> motivos pelos quais o arquivo inteiro não pode ser importado
      colunas    -> renomeadas {nome no arquivo: nome interno}, desconhecidas, opcionais_ausentes
      invalidos  -> tabela (linha, id_origem, problema): registros que serão recusados
      repetidos  -> tabela (linha, id_origem): IDs repetidos no próprio arquivo (serão ignorados)
      avisos     -> contagens de situações que não impedem a importação
      ct_desconhecidas -> CTs fora da lista conhecida
      total, validos, linhas_invalidas, linhas_repetidas
    A coluna 'linha' é o número da linha no arquivo (o cabeçalho é a linha 1).
    """
    relatorio = {
        "bloqueios": [], "total": len(df), "validos": 0,
        "linhas_invalidas": 0, "linhas_repetidas": 0,
        "colunas": {"renomeadas": {}, "desconhecidas": [], "opcionais_ausentes": []},
        "invalidos": _tabela_problemas([]), "repetidos": _tabela_problemas([]),
        "avisos": {}, "ct_desconhecidas": [],
    }

    if df.empty:
        relatorio["bloqueios"].append("O arquivo não tem nenhuma linha de dados.")
        return relatorio

    try:
        renomeado, colunas = renomear_colunas(df)
    except ValueError as erro:
        relatorio["bloqueios"].append(str(erro))
        return relatorio

    relatorio["colunas"]["renomeadas"] = colunas["renomeadas"]
    relatorio["colunas"]["desconhecidas"] = [str(nome) for nome in colunas["desconhecidas"]]
    relatorio["colunas"]["opcionais_ausentes"] = [
        c["original"] for c in COLUNAS if not c["obrigatoria"] and c["interno"] not in renomeado.columns
    ]

    for interno in colunas["obrigatorias_ausentes"]:
        relatorio["bloqueios"].append(f"Coluna obrigatória ausente: {_nome_original(interno)}")
    if relatorio["bloqueios"]:
        return relatorio

    # Problemas por registro. Primeiro, o que depende do conteúdo original das células.
    problemas = []

    def registrar(mascara, texto):
        for indice in renomeado.index[mascara.to_numpy()]:
            problemas.append((int(indice) + 2, None, texto))

    registrar(_data_ilegivel(renomeado["data_inicio"]), "Data de início ilegível")
    registrar(_data_ilegivel(renomeado["data_fim"]), "Data de fim ilegível")

    processado = aplicar_etl(renomeado)
    ids = processado["id_origem"]

    registrar(ids.isna(), "ID ausente ou inválido")
    registrar(processado["ct"].isna(), "CT ausente")
    registrar(processado["duracao_minutos"].isna(), "Duração ausente ou ilegível")
    registrar(processado["duracao_minutos"] < 0, "Duração negativa")
    registrar(
        processado["data_inicio"].isna() & ~_data_ilegivel(renomeado["data_inicio"]),
        "Início ausente e impossível de reconstruir",
    )
    registrar(processado["data_fim"] < processado["data_inicio"], "Fim anterior ao início")

    tabela = _tabela_problemas(problemas)
    tabela["id_origem"] = tabela["linha"].map(lambda linha: ids.iloc[linha - 2])
    tabela = tabela.sort_values(["linha", "problema"]).reset_index(drop=True)
    linhas_invalidas = set(tabela["linha"])

    # Repetidos no próprio arquivo (só os que não são inválidos por outro motivo).
    repetido = processado["duplicado_id"].to_numpy() & ids.notna().to_numpy()
    linhas_repetidas = [int(i) + 2 for i in processado.index[repetido] if int(i) + 2 not in linhas_invalidas]
    repetidos = _tabela_problemas([(linha, ids.iloc[linha - 2], "ID repetido no arquivo") for linha in linhas_repetidas])

    marcadores = sum(
        int(renomeado[coluna].astype(str).str.strip().isin(MARCADORES_VAZIO).sum())
        for coluna in COLUNAS_COM_MARCADOR_VAZIO if coluna in renomeado.columns
    )
    desconhecidas = processado.loc[processado["ct_desconhecido"] & processado["ct"].notna(), "ct"]

    relatorio["invalidos"] = tabela
    relatorio["repetidos"] = repetidos[["linha", "id_origem"]]
    relatorio["linhas_invalidas"] = len(linhas_invalidas)
    relatorio["linhas_repetidas"] = len(linhas_repetidas)
    relatorio["validos"] = len(processado) - len(linhas_invalidas) - len(linhas_repetidas)
    relatorio["ct_desconhecidas"] = sorted(desconhecidas.unique())
    relatorio["avisos"] = {
        "Início reconstruído (fim menos duração)": int(processado["data_inicio_reconstruida"].sum()),
        "Parada em andamento (sem data de fim)": int(processado["em_andamento"].sum()),
        "CT fora da lista conhecida": int(len(desconhecidas)),
        "Possível duplicado (mesma CT e mesmo início)": int(processado["possivel_duplicado"].sum()),
        'Células com "-" tratadas como ausentes': marcadores,
    }
    return relatorio
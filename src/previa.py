"""
Prévia da importação: mostra, antes de gravar, o que aconteceria com cada registro do arquivo.
São funções sem Streamlit e sem banco de dados, para poderem ser testadas sozinhas.
"""
import numpy as np
import pandas as pd

from src.transformer import aplicar_etl, renomear_colunas

SITUACOES = ["Novo", "Já existe no banco", "Repetido no arquivo", "Inválido"]


def problemas_por_linha(relatorio):
    """Dicionário {linha do arquivo: problemas do registro, separados por ';'}."""
    invalidos = relatorio["invalidos"]
    if invalidos.empty:
        return {}
    return invalidos.groupby("linha")["problema"].agg("; ".join).to_dict()


def montar_previa(df_lido, relatorio, ids_existentes):
    """
    Aplica o ETL ao arquivo e classifica cada registro em uma de quatro situações:
    Inválido, Repetido no arquivo, Já existe no banco ou Novo. Só os novos seriam gravados.
    ids_existentes: conjunto dos id_origem que já estão no banco.
    """
    renomeado, _ = renomear_colunas(df_lido)
    processado = aplicar_etl(renomeado)

    linhas = pd.Series(processado.index + 2, index=processado.index)  # o cabeçalho é a linha 1
    invalido = linhas.isin(relatorio["invalidos"]["linha"])
    repetido = linhas.isin(relatorio["repetidos"]["linha"]) & ~invalido
    ja_existe = processado["id_origem"].isin(ids_existentes) & ~invalido & ~repetido

    situacao = np.select(
        [invalido, repetido, ja_existe],
        ["Inválido", "Repetido no arquivo", "Já existe no banco"],
        default="Novo",
    )
    processado = processado.assign(linha_arquivo=linhas, situacao=situacao)

    novos = processado[processado["situacao"] == "Novo"]
    contagens = {nome: int((processado["situacao"] == nome).sum()) for nome in SITUACOES}

    por_ct = pd.DataFrame(columns=["ct", "paradas", "horas"])
    periodo = None
    if not novos.empty:
        por_ct = (
            novos.groupby("ct")["duracao_minutos"]
            .agg(paradas="count", horas=lambda minutos: minutos.sum() / 60)
            .reset_index()
        )
        periodo = (novos["data_inicio"].min(), novos["data_inicio"].max())

    return {
        "processado": processado,
        "contagens": contagens,
        "periodo": periodo,
        "horas_novas": float(novos["duracao_minutos"].sum() / 60) if not novos.empty else 0.0,
        "por_ct": por_ct,
    }
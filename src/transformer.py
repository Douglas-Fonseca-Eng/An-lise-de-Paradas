"""
Funções de transformação (ETL) dos dados de paradas.

Por enquanto: padronização dos nomes das colunas.
"""
import re
import unicodedata

import pandas as pd

from config.schema import COLUNAS, COLUNAS_COM_MARCADOR_VAZIO, MARCADORES_VAZIO
from config.settings import (CT_ALIASES, CTS_CONHECIDOS, LIMITE_MICROPARADA_MIN,
                             LIMITES_PARADA_LONGA_MIN)
from config.shifts import TURNOS


def normalizar_nome(nome):
    """Remove acentos, deixa minúsculo e tira tudo que não for letra ou número."""
    texto = unicodedata.normalize("NFKD", str(nome))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", texto.lower())


def _montar_mapa():
    """Cria o dicionário: nome normalizado -> nome interno."""
    mapa = {}
    for coluna in COLUNAS:
        for variante in (coluna["original"], coluna["interno"]):
            chave = normalizar_nome(variante)
            if chave in mapa and mapa[chave] != coluna["interno"]:
                raise ValueError(f"Conflito no schema: '{chave}' aponta para duas colunas internas")
            mapa[chave] = coluna["interno"]
    return mapa


MAPA_NOMES = _montar_mapa()


def renomear_colunas(df):
    """
    Renomeia as colunas do DataFrame para os nomes internos.
    Devolve (df_renomeado, relatorio).
    """
    renomeadas = {}
    desconhecidas = []

    for nome in df.columns:
        interno = MAPA_NOMES.get(normalizar_nome(nome))
        if interno is None:
            desconhecidas.append(nome)
        else:
            renomeadas[nome] = interno

    internos = list(renomeadas.values())
    repetidas = sorted({i for i in internos if internos.count(i) > 1})
    if repetidas:
        raise ValueError(f"Mais de uma coluna do arquivo corresponde a: {repetidas}")

    df_novo = df.rename(columns=renomeadas)

    obrigatorias = [c["interno"] for c in COLUNAS if c["obrigatoria"]]
    ausentes = [c for c in obrigatorias if c not in df_novo.columns]

    relatorio = {
        "renomeadas": renomeadas,
        "desconhecidas": desconhecidas,
        "obrigatorias_ausentes": ausentes,
    }
    return df_novo, relatorio


def padronizar_duracao(df):
    """Converte a duração para tempo de verdade e cria duracao_segundos e duracao_minutos."""
    df = df.copy()
    df["duracao"] = pd.to_timedelta(df["duracao"], errors="coerce")
    df["duracao_segundos"] = df["duracao"].dt.total_seconds()
    df["duracao_minutos"] = df["duracao_segundos"] / 60
    return df


def padronizar_datas(df):
    """
    Converte data_inicio e data_fim para data/hora e aplica as regras aprovadas:
    - Regra B: início ausente é reconstruído como data_fim - duracao (e marcado).
    - Regra C: fim ausente com início válido = parada em andamento (fim não é inventado).
    """
    df = df.copy()
    inicio = pd.to_datetime(df["data_inicio"], format="mixed", errors="coerce")
    fim = pd.to_datetime(df["data_fim"], format="mixed", errors="coerce")
    duracao = pd.to_timedelta(df["duracao"], errors="coerce")

    reconstruir = inicio.isna() & fim.notna() & duracao.notna()
    inicio = inicio.where(~reconstruir, fim - duracao)

    df["data_inicio"] = inicio
    df["data_fim"] = fim
    df["data_inicio_reconstruida"] = reconstruir
    df["em_andamento"] = fim.isna() & inicio.notna()
    return df


COLUNAS_TEXTO = [c["interno"] for c in COLUNAS if c["tipo"] == "texto"]


def limpar_texto(df):
    """Tira espaços nas pontas, reduz espaços repetidos e transforma texto vazio em ausente."""
    df = df.copy()
    for coluna in COLUNAS_TEXTO:
        if coluna in df.columns and pd.api.types.is_string_dtype(df[coluna]):
            serie = df[coluna].str.strip().str.replace(r"\s+", " ", regex=True)
            df[coluna] = serie.replace("", pd.NA)
    return df


def padronizar_ct(df):
    """
    Deixa o CT em maiúsculas, sem espaços nas pontas, e aplica apenas os apelidos
    confirmados (CT_ALIASES). Cria ct_desconhecido = True para CT fora da lista conhecida.
    """
    df = df.copy()
    ct = df["ct"].astype("string").str.strip().str.upper()
    df["ct"] = ct.replace(CT_ALIASES)
    df["ct_desconhecido"] = ~df["ct"].isin(CTS_CONHECIDOS)
    return df


TIPOS = {c["interno"]: c["tipo"] for c in COLUNAS}


def tratar_ausentes(df):
    """
    Regra A (aprovada): nas colunas listadas em COLUNAS_COM_MARCADOR_VAZIO,
    o marcador "-" passa a ser valor ausente de verdade (NA).
    Colunas de tipo inteiro viram número (Int64, que aceita ausentes).
    """
    df = df.copy()
    for coluna in COLUNAS_COM_MARCADOR_VAZIO:
        if coluna not in df.columns:
            continue
        e_marcador = df[coluna].astype(str).str.strip().isin(MARCADORES_VAZIO)
        df[coluna] = df[coluna].where(~e_marcador, pd.NA)
        if TIPOS.get(coluna) == "inteiro":
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce").astype("Int64")
    return df


def marcar_duplicados(df):
    """
    Marca (sem apagar nada) registros repetidos dentro do arquivo:
    - duplicado_id: o id_origem já apareceu antes no arquivo.
    - possivel_duplicado: mesmo CT e mesma data_inicio de um registro anterior (conferir).
    """
    df = df.copy()
    df["duplicado_id"] = df["id_origem"].duplicated(keep="first")
    tem_inicio = df["data_inicio"].notna()
    repetiu_ct_inicio = df.duplicated(subset=["ct", "data_inicio"], keep="first")
    df["possivel_duplicado"] = repetiu_ct_inicio & tem_inicio
    return df


def _minutos_do_dia(hora):
    """Converte um horário em minutos desde a meia-noite (ex.: 05:30 -> 330)."""
    return hora.hour * 60 + hora.minute + hora.second / 60


def atribuir_turno(df):
    """
    Cria turno e data_operacional a partir de data_inicio.
    Turnos que atravessam a meia-noite pertencem à data em que o turno começou.
    """
    df = df.copy()
    inicio = df["data_inicio"]
    minutos = inicio.dt.hour * 60 + inicio.dt.minute + inicio.dt.second / 60

    turno = pd.Series(pd.NA, index=df.index, dtype="string")
    data_op = inicio.dt.normalize()

    for t in TURNOS:
        ini = _minutos_do_dia(t["inicio"])
        fim = _minutos_do_dia(t["fim"])
        if ini < fim:
            no_turno = (minutos >= ini) & (minutos < fim)
        else:
            no_turno = (minutos >= ini) | (minutos < fim)
            depois_da_meia_noite = no_turno & (minutos < fim)
            data_op = data_op.where(~depois_da_meia_noite, data_op - pd.Timedelta(days=1))
        turno = turno.where(~no_turno, t["nome"])

    df["turno"] = turno
    df["data_operacional"] = data_op
    return df


def _rotulos_faixas(limites):
    """Monta os nomes das faixas de duração a partir dos limites (ex.: 'até 1 min', '1 a 5 min')."""
    rotulos = [f"até {limites[0]:g} min"]
    for menor, maior in zip(limites[:-1], limites[1:]):
        rotulos.append(f"{menor:g} a {maior:g} min")
    rotulos.append(f"acima de {limites[-1]:g} min")
    return rotulos


def criar_features_basicas(df):
    """
    Cria colunas derivadas simples:
    hora_inicio, dia_semana (0 = segunda ... 6 = domingo), microparada,
    faixa_duracao e intervalo_anterior_min (minutos desde o fim da parada anterior da mesma CT).
    """
    df = df.copy()
    inicio = df["data_inicio"]

    df["hora_inicio"] = inicio.dt.hour.astype("Int64")
    df["dia_semana"] = inicio.dt.dayofweek.astype("Int64")

    df["microparada"] = df["duracao_minutos"] <= LIMITE_MICROPARADA_MIN

    limites = sorted(set([LIMITE_MICROPARADA_MIN] + LIMITES_PARADA_LONGA_MIN))
    df["faixa_duracao"] = pd.cut(
        df["duracao_minutos"],
        bins=[0] + limites + [float("inf")],
        labels=_rotulos_faixas(limites),
        include_lowest=True,
    )

    ordenado = df.sort_values(["ct", "data_inicio"])
    fim_anterior = ordenado.groupby("ct")["data_fim"].shift()
    intervalo = (ordenado["data_inicio"] - fim_anterior).dt.total_seconds() / 60
    df["intervalo_anterior_min"] = intervalo
    return df
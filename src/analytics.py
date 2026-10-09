"""
Camada analítica: lê os dados do banco e os deixa prontos para o dashboard.
"""
import numpy as np
import pandas as pd
from sqlalchemy import func, select

from config.settings import LIMITES_PARADA_LONGA_MIN
from config.shifts import TURNOS
from src.filters import ROTULO_NAO_INFORMADO, opcoes_da_coluna
from src.tabelas import arquivos_importados, paradas
from src.transformer import criar_features_basicas
from src.utils import formatar_decimal

COLUNAS_DATA = ["data_inicio", "data_fim", "data_operacional", "data_importacao"]
COLUNAS_FLAG = ["data_inicio_reconstruida", "em_andamento", "ct_desconhecido", "possivel_duplicado"]


def preparar_dataframe(df):
    """Garante os tipos certos e calcula as colunas derivadas que não ficam no banco."""
    df = df.copy()
    for coluna in COLUNAS_DATA:
        df[coluna] = pd.to_datetime(df[coluna])
    for coluna in COLUNAS_FLAG:
        df[coluna] = df[coluna].fillna(False).astype(bool)
    df = criar_features_basicas(df)
    return df.sort_values("data_inicio").reset_index(drop=True)


def carregar_paradas(engine):
    """Lê todas as paradas do banco e devolve o DataFrame pronto para análise."""
    with engine.connect() as conexao:
        df = pd.read_sql(select(paradas), conexao)
    return preparar_dataframe(df)


def obter_versao_dados(engine):
    """Número que muda a cada nova importação (usado para renovar o cache do dashboard)."""
    with engine.connect() as conexao:
        ultimo = conexao.execute(select(func.max(arquivos_importados.c.id))).scalar()
    return ultimo or 0


def calcular_kpis(df):
    """Indicadores da visão geral. Todas as durações em minutos."""
    total = len(df)
    duracao = df["duracao_minutos"]
    return {
        "total_paradas": total,
        "maquinas": int(df["ct"].nunique()),
        "tempo_total_min": float(duracao.sum()),
        "media_min": float(duracao.mean()) if total else None,
        "mediana_min": float(duracao.median()) if total else None,
        "maior_min": float(duracao.max()) if total else None,
        "microparadas": int(df["microparada"].sum()),
        "acima_de": {limite: int((duracao > limite).sum()) for limite in LIMITES_PARADA_LONGA_MIN},
        "em_andamento": int(df["em_andamento"].sum()),
    }


def resumo_por_grupo(df, coluna):
    """
    Quantidade de paradas e tempo parado por grupo (máquina, turno, origem etc.),
    com a participação de cada grupo no total, em %.
    """
    grupos = df[coluna].astype("object")
    grupos = grupos.where(grupos.notna(), ROTULO_NAO_INFORMADO).astype(str)

    resumo = (
        df.groupby(grupos, observed=True)["duracao_minutos"]
        .agg(paradas="count", tempo_min="sum", media_min="mean", mediana_min="median")
        .reset_index()
        .rename(columns={coluna: "grupo"})
    )

    ordem = opcoes_da_coluna(df, coluna)
    resumo["grupo"] = pd.Categorical(resumo["grupo"], categories=ordem, ordered=True)
    resumo = resumo.sort_values("grupo").reset_index(drop=True)
    resumo["grupo"] = resumo["grupo"].astype(str)

    resumo["tempo_horas"] = resumo["tempo_min"] / 60
    resumo["pct_paradas"] = resumo["paradas"] / resumo["paradas"].sum() * 100
    resumo["pct_tempo"] = resumo["tempo_min"] / resumo["tempo_min"].sum() * 100
    return resumo


def destaque_participacao(resumo, limite_pontos=5):
    """Frase com a maior diferença entre a participação no tempo parado e na quantidade."""
    if len(resumo) < 2:
        return "Há só um grupo na seleção atual. Escolha outra comparação ou limpe os filtros."

    diferenca = resumo["pct_tempo"] - resumo["pct_paradas"]
    if diferenca.max() < limite_pontos:
        return "Quantidade de paradas e tempo parado estão distribuídos de forma parecida entre os grupos."

    linha = resumo.loc[diferenca.idxmax()]
    return (
        f"{linha['grupo']} responde por {formatar_decimal(linha['pct_paradas'])}% das paradas, "
        f"mas por {formatar_decimal(linha['pct_tempo'])}% do tempo parado."
    )


def serie_temporal(df, frequencia="D", separar_por=None):
    """
    Quantidade de paradas e horas paradas por período, completando com zero os períodos sem paradas.
    frequencia: "D" (dia) ou "W" (semana, de segunda a domingo).
    O tempo de cada parada é contado inteiro no período em que ela começou.
    Devolve colunas: periodo, grupo, paradas, horas ("grupo" é "Total" quando não há separação).
    """
    dados = df.copy()
    dados["periodo"] = dados["data_inicio"].dt.to_period(frequencia).dt.start_time
    dados["grupo"] = dados[separar_por].astype(str) if separar_por else "Total"

    resumo = (
        dados.groupby(["periodo", "grupo"])["duracao_minutos"]
        .agg(paradas="count", minutos="sum")
        .reset_index()
    )
    resumo["horas"] = resumo["minutos"] / 60

    passo = "D" if frequencia == "D" else "W-MON"
    periodos = pd.date_range(resumo["periodo"].min(), resumo["periodo"].max(), freq=passo)
    grupos = sorted(resumo["grupo"].unique())
    grade = pd.MultiIndex.from_product([periodos, grupos], names=["periodo", "grupo"]).to_frame(index=False)

    completo = grade.merge(resumo, on=["periodo", "grupo"], how="left")
    completo[["paradas", "minutos", "horas"]] = completo[["paradas", "minutos", "horas"]].fillna(0)
    return completo.drop(columns="minutos")


def picos_temporais(serie):
    """Período com mais paradas e período com mais tempo parado (somando os grupos)."""
    total = serie.groupby("periodo")[["paradas", "horas"]].sum()
    return {
        "periodo_paradas": total["paradas"].idxmax(),
        "max_paradas": int(total["paradas"].max()),
        "periodo_horas": total["horas"].idxmax(),
        "max_horas": float(total["horas"].max()),
    }


def horas_de_turno_no_periodo(inicio, fim):
    """Quantas horas de cada turno existem dentro da janela de tempo [inicio, fim]."""
    horas = {t["nome"]: 0.0 for t in TURNOS}
    dias = pd.date_range(inicio.normalize() - pd.Timedelta(days=1), fim.normalize(), freq="D")
    for dia in dias:
        for t in TURNOS:
            comeco = dia + pd.Timedelta(hours=t["inicio"].hour, minutes=t["inicio"].minute)
            termino = dia + pd.Timedelta(hours=t["fim"].hour, minutes=t["fim"].minute)
            if termino <= comeco:  # turno que atravessa a meia-noite
                termino += pd.Timedelta(days=1)
            sobreposicao = min(termino, fim) - max(comeco, inicio)
            horas[t["nome"]] += max(sobreposicao.total_seconds(), 0) / 3600
    return horas


def resumo_turnos(df, horas_turno, separar_por_ct=False):
    """
    Indicadores por turno (e por CT, se pedido): quantidade, tempo, média, mediana,
    microparadas, paradas acima dos limites e taxas por hora de turno.
    horas_turno: dicionário {turno: horas de turno no período} (veja horas_de_turno_no_periodo).
    """
    dados = df.copy()
    dados["grupo"] = dados["ct"].astype(str) if separar_por_ct else "Todas"

    agregados = {
        "paradas": ("duracao_minutos", "count"),
        "tempo_min": ("duracao_minutos", "sum"),
        "media_min": ("duracao_minutos", "mean"),
        "mediana_min": ("duracao_minutos", "median"),
        "microparadas": ("microparada", "sum"),
    }
    for limite in LIMITES_PARADA_LONGA_MIN:
        dados[f"acima_{limite}"] = dados["duracao_minutos"] > limite
        agregados[f"acima_{limite}"] = (f"acima_{limite}", "sum")

    resumo = dados.groupby(["turno", "grupo"]).agg(**agregados).reset_index()

    ordem = [t["nome"] for t in TURNOS]
    resumo["turno"] = pd.Categorical(resumo["turno"], categories=ordem, ordered=True)
    resumo = resumo.sort_values(["grupo", "turno"]).reset_index(drop=True)
    resumo["turno"] = resumo["turno"].astype(str)

    resumo["tempo_horas"] = resumo["tempo_min"] / 60
    resumo["horas_turno"] = resumo["turno"].map(horas_turno)
    resumo["paradas_por_hora"] = resumo["paradas"] / resumo["horas_turno"].where(resumo["horas_turno"] > 0)
    return resumo


def janela_de_analise(df_completo, periodo=None):
    """
    Janela de tempo (início, fim) coberta pelos dados ou pelo período escolhido no filtro.
    O fim dos dados é o instante em que terminou a última parada (início + duração),
    o que também cobre a parada que ainda estava em andamento na exportação.
    """
    fim_dados = (df_completo["data_inicio"] + pd.to_timedelta(df_completo["duracao_minutos"], unit="m")).max()
    if periodo is None:
        return df_completo["data_inicio"].min().normalize(), fim_dados

    inicio = pd.Timestamp(periodo[0])
    fim = min(pd.Timestamp(periodo[1]) + pd.Timedelta(days=1), fim_dados)
    return inicio, fim


def pareto(df, coluna, medida="paradas", ocultar_nao_informado=False):
    """
    Tabela de Pareto: categorias da maior para a menor, com a participação (%)
    e o percentual acumulado. medida: "paradas" ou "tempo_horas".
    """
    resumo = resumo_por_grupo(df, coluna)
    if ocultar_nao_informado:
        resumo = resumo[resumo["grupo"] != ROTULO_NAO_INFORMADO]

    resumo = resumo.sort_values(medida, ascending=False, kind="stable").reset_index(drop=True)
    total = resumo[medida].sum()
    resumo["valor"] = resumo[medida]
    resumo["pct"] = resumo["valor"] / total * 100 if total else 0.0
    resumo["pct_acumulado"] = resumo["pct"].cumsum()
    resumo.insert(0, "posicao", range(1, len(resumo) + 1))
    return resumo


def categorias_ate_percentual(resumo, alvo=80):
    """Quantas categorias (das maiores) são necessárias para somar pelo menos 'alvo' %."""
    if resumo.empty:
        return 0
    return min(int((resumo["pct_acumulado"] < alvo).sum()) + 1, len(resumo))


DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


def horas_de_exposicao_por_slot(inicio, fim):
    """
    Quantas horas existem, na janela [inicio, fim], para cada combinação de
    dia da semana (linhas 0 a 6) e hora do dia (colunas 0 a 23).
    """
    slots = pd.date_range(inicio.floor("h"), fim.ceil("h"), freq="h", inclusive="left")
    comeco = slots.to_series()
    sobreposicao = (comeco + pd.Timedelta(hours=1)).clip(upper=fim) - comeco.clip(lower=inicio)
    horas = (sobreposicao.dt.total_seconds() / 3600).clip(lower=0)

    exposicao = pd.DataFrame({"dia": slots.dayofweek, "hora": slots.hour, "horas": horas.to_numpy()})
    matriz = exposicao.pivot_table(index="dia", columns="hora", values="horas", aggfunc="sum", fill_value=0)
    return matriz.reindex(index=range(7), columns=range(24), fill_value=0)


def matriz_calor(df, medida, inicio, fim, normalizar=False):
    """
    Matriz 7 (dia da semana) x 24 (hora de início) com a medida escolhida.
    medida: "paradas" ou "tempo_horas". Com normalizar=True, divide pelo número de vezes que cada
    combinação de dia e hora ocorreu na janela (resultado: média por ocorrência).
    """
    if medida == "paradas":
        valores = df.groupby(["dia_semana", "hora_inicio"]).size()
    else:
        valores = df.groupby(["dia_semana", "hora_inicio"])["duracao_minutos"].sum() / 60

    matriz = valores.unstack("hora_inicio").reindex(index=range(7), columns=range(24)).fillna(0)
    if normalizar:
        exposicao = horas_de_exposicao_por_slot(inicio, fim)
        matriz = matriz / exposicao.where(exposicao > 0)
    matriz.index = DIAS_SEMANA
    return matriz


def intervalos_entre_microparadas(df_micro):
    """Minutos entre o fim de uma microparada e o início da seguinte, na mesma CT."""
    ordenado = df_micro.sort_values(["ct", "data_inicio"])
    fim_anterior = ordenado.groupby("ct")["data_fim"].shift()
    intervalos = (ordenado["data_inicio"] - fim_anterior).dt.total_seconds() / 60
    return intervalos.dropna()


def detectar_rajadas(df_micro, lacuna_max_min=10, minimo=5):
    """
    Agrupa microparadas seguidas da mesma CT em rajadas: uma nova rajada começa quando o intervalo
    até a microparada anterior passa de lacuna_max_min. Devolve só as rajadas com pelo menos
    'minimo' microparadas, da maior para a menor.
    """
    linhas = []
    for ct, grupo in df_micro.sort_values("data_inicio").groupby("ct"):
        lacuna = (grupo["data_inicio"] - grupo["data_fim"].shift()).dt.total_seconds() / 60
        numero_da_rajada = (lacuna.isna() | (lacuna > lacuna_max_min)).cumsum()
        for _, parte in grupo.groupby(numero_da_rajada):
            linhas.append({
                "ct": ct,
                "inicio": parte["data_inicio"].min(),
                "fim": parte["data_fim"].max(),
                "microparadas": len(parte),
            })

    rajadas = pd.DataFrame(linhas, columns=["ct", "inicio", "fim", "microparadas"])
    rajadas["inicio"] = pd.to_datetime(rajadas["inicio"])
    rajadas["fim"] = pd.to_datetime(rajadas["fim"])
    rajadas["duracao_min"] = (rajadas["fim"] - rajadas["inicio"]).dt.total_seconds() / 60
    rajadas = rajadas[rajadas["microparadas"] >= minimo]
    return rajadas.sort_values("microparadas", ascending=False, kind="stable").reset_index(drop=True)


def resumo_janelas(df_micro, janelas=(10, 20, 30, 40, 60, 120), minimo=5):
    """
    Para cada microparada, conta quantas microparadas da mesma CT aconteceram nos N minutos
    anteriores (sem contar ela mesma) e resume por janela: média, percentil 90, máximo e
    percentual de microparadas com 'minimo' ou mais microparadas anteriores.
    """
    colunas = ["janela_min", "media", "p90", "maximo", "pct_minimo"]
    if df_micro.empty:
        return pd.DataFrame(columns=colunas)

    inicios_por_ct = [
        grupo["data_inicio"].sort_values().to_numpy().astype("datetime64[s]").astype("int64")
        for _, grupo in df_micro.groupby("ct")
    ]

    linhas = []
    for janela in janelas:
        contagens = np.concatenate([
            np.arange(len(t)) - np.searchsorted(t, t - janela * 60, side="left")
            for t in inicios_por_ct
        ])
        linhas.append({
            "janela_min": janela,
            "media": contagens.mean(),
            "p90": np.percentile(contagens, 90),
            "maximo": contagens.max(),
            "pct_minimo": (contagens >= minimo).mean() * 100,
        })
    return pd.DataFrame(linhas, columns=colunas)


def serie_horaria(df, dia):
    """Quantidade de paradas por hora e por CT em um dia, com zero nas horas sem paradas."""
    dados = df[df["data_inicio"].dt.date == dia]
    horas = pd.date_range(pd.Timestamp(dia), periods=24, freq="h")
    contagem = dados.groupby([dados["data_inicio"].dt.floor("h"), "ct"]).size().unstack(fill_value=0)
    contagem = contagem.reindex(horas, fill_value=0)
    return contagem.reset_index(names="periodo").melt(id_vars="periodo", var_name="grupo", value_name="paradas")
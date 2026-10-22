"""
Filtros globais do dashboard: opções disponíveis e aplicação ao DataFrame.
São funções sem Streamlit, para poderem ser testadas sozinhas.
"""
import pandas as pd

from config.settings import LIMITES_PARADA_LONGA_MIN
from src.utils import rotulo_limite

ROTULO_NAO_INFORMADO = "Não informado"

# (coluna, rótulo mostrado na tela)
FILTROS_PRINCIPAIS = [
    ("ct", "Máquina (CT)"),
    ("turno", "Turno"),
    ("faixa_duracao", "Faixa de duração"),
]
FILTROS_ADICIONAIS = [
    ("motivo", "Motivo"),
    ("origem", "Origem"),
    ("tag", "Tag"),
    ("operador", "Operador"),
    ("area_responsavel", "Área responsável"),
]

OPCOES_QUEBRA = ["Todas", "Somente quebras", "Sem quebras"]


def opcoes_da_coluna(df, coluna):
    """Valores disponíveis para o filtro, em ordem. Ausentes aparecem como 'Não informado'."""
    serie = df[coluna]
    if isinstance(serie.dtype, pd.CategoricalDtype):
        valores = [str(v) for v in serie.cat.categories]
    else:
        valores = sorted(serie.dropna().astype(str).unique())
    if serie.isna().any():
        valores.append(ROTULO_NAO_INFORMADO)
    return valores


def aplicar_filtros(df, filtros):
    """
    Aplica os filtros e devolve só as paradas selecionadas.

    filtros é um dicionário com:
      "periodo":    (data_inicial, data_final) ou None
      "categoricos": {coluna: [valores escolhidos]}  (lista vazia = sem filtro)
      "quebra":     uma das OPCOES_QUEBRA
    """
    mascara = pd.Series(True, index=df.index)

    periodo = filtros.get("periodo")
    if periodo:
        inicio = pd.Timestamp(periodo[0])
        fim = pd.Timestamp(periodo[1])
        datas = df["data_inicio"].dt.normalize()
        mascara &= (datas >= inicio) & (datas <= fim)

    for coluna, escolhidos in filtros.get("categoricos", {}).items():
        if escolhidos:
            serie = df[coluna].astype("object")
            serie = serie.where(serie.notna(), ROTULO_NAO_INFORMADO).astype(str)
            mascara &= serie.isin(escolhidos)

    quebra = filtros.get("quebra", OPCOES_QUEBRA[0])
    if quebra == "Somente quebras":
        mascara &= (df["quebra"] == 1).fillna(False).astype(bool)
    elif quebra == "Sem quebras":
        mascara &= (df["quebra"] == 0).fillna(False).astype(bool)

    return df[mascara]


COLUNAS_BUSCA = ["motivo", "origem", "tag", "descricao_tag", "operador", "area_responsavel", "providencia"]


def opcoes_recorte():
    """Recortes que levam de um indicador do dashboard às paradas responsáveis por ele."""
    limites = [f"Acima de {rotulo_limite(limite)}" for limite in LIMITES_PARADA_LONGA_MIN]
    return ["Todas as paradas", "Microparadas"] + limites + ["Em andamento", "Início reconstruído"]


def aplicar_recorte(df, recorte):
    """Devolve só as paradas do recorte escolhido (mesmas definições dos indicadores)."""
    if recorte == "Microparadas":
        return df[df["microparada"]]
    for limite in LIMITES_PARADA_LONGA_MIN:
        if recorte == f"Acima de {rotulo_limite(limite)}":
            return df[df["duracao_minutos"] > limite]
    if recorte == "Em andamento":
        return df[df["em_andamento"]]
    if recorte == "Início reconstruído":
        return df[df["data_inicio_reconstruida"]]
    return df


def buscar_texto(df, texto, colunas=COLUNAS_BUSCA):
    """Mantém as paradas em que o texto aparece em alguma das colunas (sem diferenciar maiúsculas)."""
    texto = (texto or "").strip()
    if not texto:
        return df
    mascara = pd.Series(False, index=df.index)
    for coluna in colunas:
        textos = df[coluna].astype("object").fillna("").astype(str)
        mascara |= textos.str.contains(texto, case=False, regex=False)
    return df[mascara]


def periodo_apos_nova_importacao(selecionado, intervalo_anterior, intervalo_atual):
    """
    Decide o período do filtro quando a base de dados pode ter crescido.
    Se o usuário estava vendo o período completo dos dados e o intervalo mudou, acompanha o novo
    intervalo. Se ele tinha escolhido um período próprio, mantém a escolha.
    """
    if (intervalo_anterior is not None and intervalo_anterior != intervalo_atual
            and tuple(selecionado) == intervalo_anterior):
        return intervalo_atual
    return selecionado
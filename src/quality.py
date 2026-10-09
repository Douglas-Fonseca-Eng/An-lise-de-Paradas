"""
Verificações de qualidade dos dados gravados no banco.
São funções sem Streamlit, para poderem ser testadas sozinhas.
"""
import pandas as pd

from src.transformer import normalizar_nome

# Colunas de dados (sem identificadores, datas de importação e marcas do ETL).
COLUNAS_DADOS = [
    "planta", "ct", "data_inicio", "data_fim", "quebra", "frequencia", "origem", "tag",
    "descricao_tag", "equipamento", "modo_falha", "causa_raiz", "motivo", "providencia", "acm",
    "nota_corretiva", "operador", "area_responsavel", "ultimo_usuario",
    "duracao_minutos", "turno", "data_operacional",
]

COLUNAS_CATEGORICAS = [
    "planta", "ct", "origem", "tag", "descricao_tag", "motivo", "providencia",
    "operador", "area_responsavel", "ultimo_usuario", "turno",
]


def tabela_ausentes(df):
    """Quantidade e percentual de valores ausentes por coluna, da mais vazia para a menos."""
    ausentes = df[COLUNAS_DADOS].isna().sum()
    resumo = pd.DataFrame({
        "coluna": ausentes.index,
        "ausentes": ausentes.to_numpy(),
        "pct_ausentes": (ausentes / len(df) * 100).to_numpy() if len(df) else 0.0,
    })
    return resumo.sort_values(["pct_ausentes", "coluna"], ascending=[False, True]).reset_index(drop=True)


def colunas_totalmente_vazias(df):
    """Nomes das colunas de dados em que todos os valores estão ausentes."""
    if df.empty:
        return []
    return [coluna for coluna in COLUNAS_DADOS if df[coluna].isna().all()]


def categorias_inconsistentes(df, colunas=COLUNAS_CATEGORICAS):
    """
    Procura valores que parecem o mesmo, mas estão escritos de formas diferentes
    (maiúsculas, acentos, espaços, símbolos). Devolve uma linha por grupo de variantes.
    """
    linhas = []
    for coluna in colunas:
        contagem = df[coluna].dropna().astype(str).value_counts()
        grupos = {}
        for valor, quantidade in contagem.items():
            grupos.setdefault(normalizar_nome(valor), []).append((valor, quantidade))
        for variantes in grupos.values():
            if len(variantes) > 1:
                linhas.append({
                    "coluna": coluna,
                    "variantes": " | ".join(valor for valor, _ in variantes),
                    "registros": sum(quantidade for _, quantidade in variantes),
                })
    return pd.DataFrame(linhas, columns=["coluna", "variantes", "registros"])


def verificacoes(df):
    """
    Lista de verificações de consistência: (verificação, quantidade, observação).
    Quantidade zero significa que o problema não existe.
    """
    fim_antes_inicio = (df["data_fim"] < df["data_inicio"]).sum()
    sobrepostas = (df["intervalo_anterior_min"] < 0).sum()
    return pd.DataFrame([
        ("IDs repetidos no banco", int(df["id_origem"].duplicated().sum()), "O banco impede repetição."),
        ("Possíveis duplicados (mesma CT e mesmo início)", int(df["possivel_duplicado"].sum()), "Podem ser a mesma parada com ID diferente."),
        ("Início ausente ou inválido", int(df["data_inicio"].isna().sum()), ""),
        ("Fim ausente", int(df["data_fim"].isna().sum()), "Parada em andamento na exportação (regra C)."),
        ("Início reconstruído", int(df["data_inicio_reconstruida"].sum()), "Início calculado como fim menos duração (regra B)."),
        ("Duração negativa", int((df["duracao_minutos"] < 0).sum()), ""),
        ("Duração zero", int((df["duracao_minutos"] == 0).sum()), ""),
        ("Fim anterior ao início", int(fim_antes_inicio), ""),
        ("Paradas sobrepostas na mesma CT", int(sobrepostas), "Início antes do fim da parada anterior."),
        ("CT fora da lista conhecida", int(df["ct_desconhecido"].sum()), "Veja CTS_CONHECIDOS em config/settings.py."),
    ], columns=["verificacao", "quantidade", "observacao"])
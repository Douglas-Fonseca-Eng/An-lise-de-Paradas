"""
Importação de planilhas para o banco de dados.

Fluxo: ler a planilha -> aplicar o ETL -> separar registros novos dos já
existentes -> gravar tudo em uma única transação (ou grava tudo, ou nada).
"""
import hashlib
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import insert, select

from src.tabelas import arquivos_importados, paradas
from src.transformer import aplicar_etl, renomear_colunas

# Colunas do DataFrame que vão para a tabela "paradas".
COLUNAS_PARADAS = [
    "id_origem", "planta", "ct", "data_inicio", "data_fim", "quebra", "frequencia",
    "origem", "tag", "descricao_tag", "equipamento", "modo_falha", "causa_raiz", "motivo",
    "providencia", "acm", "nota_corretiva", "operador", "area_responsavel", "ultimo_usuario",
    "duracao_segundos", "duracao_minutos", "turno", "data_operacional",
    "data_inicio_reconstruida", "em_andamento", "ct_desconhecido", "possivel_duplicado",
]


def calcular_hash(caminho):
    """Impressão digital (SHA-256) do conteúdo do arquivo."""
    sha = hashlib.sha256()
    with open(caminho, "rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            sha.update(bloco)
    return sha.hexdigest()


def processar_planilha(caminho):
    """Lê a planilha e aplica toda a cadeia do ETL. Devolve o DataFrame pronto."""
    df = pd.read_excel(caminho, sheet_name="Paradas")
    df, relatorio = renomear_colunas(df)
    if relatorio["obrigatorias_ausentes"]:
        raise ValueError(f"Colunas obrigatórias ausentes: {relatorio['obrigatorias_ausentes']}")
    return aplicar_etl(df)


def classificar_registros(df, ids_existentes):
    """
    Separa os registros em quatro grupos que não se sobrepõem:
    inválidos, repetidos no próprio arquivo, já existentes no banco e novos.
    """
    invalido = df["id_origem"].isna() | df["ct"].isna()
    repetido = df["duplicado_id"] & ~invalido
    ja_existe = df["id_origem"].isin(ids_existentes) & ~invalido & ~repetido
    novo = ~(invalido | repetido | ja_existe)
    return invalido, repetido, ja_existe, novo


def _para_python(valor):
    """Converte valores do Pandas/NumPy para tipos simples do Python (ausente vira None)."""
    if pd.isna(valor):
        return None
    if isinstance(valor, pd.Timestamp):
        return valor.to_pydatetime()
    if hasattr(valor, "item"):
        return valor.item()
    return valor


def preparar_registros(df, arquivo_id, data_importacao):
    """Transforma o DataFrame em uma lista de dicionários pronta para gravar no banco."""
    registros = []
    for linha in df[COLUNAS_PARADAS].to_dict("records"):
        registro = {nome: _para_python(valor) for nome, valor in linha.items()}
        if registro["data_operacional"] is not None:
            registro["data_operacional"] = registro["data_operacional"].date()
        registro["arquivo_id"] = arquivo_id
        registro["data_importacao"] = data_importacao
        registros.append(registro)
    return registros


def importar_planilha(caminho, engine):
    """
    Importa uma planilha para o banco. Só grava registros novos e nunca sobrescreve nada.
    Devolve um dicionário com o resumo do que aconteceu.
    """
    caminho = Path(caminho)
    hash_arquivo = calcular_hash(caminho)

    with engine.begin() as conexao:  # transação: se algo falhar, nada é gravado
        ja_importado = conexao.execute(
            select(arquivos_importados.c.id).where(arquivos_importados.c.hash_arquivo == hash_arquivo)
        ).first()
        if ja_importado is not None:
            return {"status": "arquivo_ja_importado", "arquivo_id": ja_importado[0]}

        df = processar_planilha(caminho)
        ids_existentes = set(conexao.execute(select(paradas.c.id_origem)).scalars())
        invalido, repetido, ja_existe, novo = classificar_registros(df, ids_existentes)

        resumo = {
            "status": "importado",
            "total": len(df),
            "novos": int(novo.sum()),
            "ja_existentes": int(ja_existe.sum()),
            "repetidos_no_arquivo": int(repetido.sum()),
            "invalidos": int(invalido.sum()),
        }

        agora = datetime.now()
        resultado = conexao.execute(insert(arquivos_importados).values(
            nome_arquivo=caminho.name,
            hash_arquivo=hash_arquivo,
            data_importacao=agora,
            total_registros=resumo["total"],
            registros_importados=resumo["novos"],
            registros_ignorados=resumo["total"] - resumo["novos"],
            observacoes=(f"ja_existentes={resumo['ja_existentes']}; "
                         f"repetidos_no_arquivo={resumo['repetidos_no_arquivo']}; "
                         f"invalidos={resumo['invalidos']}"),
        ))
        arquivo_id = resultado.inserted_primary_key[0]
        resumo["arquivo_id"] = arquivo_id

        registros = preparar_registros(df[novo], arquivo_id, agora)
        if registros:
            conexao.execute(insert(paradas), registros)

    return resumo


def listar_arquivos_importados(engine):
    """Histórico das importações, da mais recente para a mais antiga."""
    consulta = select(
        arquivos_importados.c.id,
        arquivos_importados.c.nome_arquivo,
        arquivos_importados.c.data_importacao,
        arquivos_importados.c.total_registros,
        arquivos_importados.c.registros_importados,
        arquivos_importados.c.registros_ignorados,
        arquivos_importados.c.observacoes,
    ).order_by(arquivos_importados.c.data_importacao.desc(), arquivos_importados.c.id.desc())

    with engine.connect() as conexao:
        return pd.read_sql(consulta, conexao)


def calcular_hash_conteudo(conteudo):
    """Impressão digital (SHA-256) de um conteúdo em memória. Igual à do arquivo com o mesmo conteúdo."""
    return hashlib.sha256(conteudo).hexdigest()


def obter_ids_existentes(engine):
    """Conjunto dos id_origem que já estão gravados no banco."""
    with engine.connect() as conexao:
        return set(conexao.execute(select(paradas.c.id_origem)).scalars())


def buscar_arquivo_importado(engine, hash_arquivo):
    """Dados do arquivo já importado com este conteúdo, ou None se ele nunca foi importado."""
    consulta = select(
        arquivos_importados.c.id,
        arquivos_importados.c.nome_arquivo,
        arquivos_importados.c.data_importacao,
    ).where(arquivos_importados.c.hash_arquivo == hash_arquivo)
    with engine.connect() as conexao:
        linha = conexao.execute(consulta).first()
    if linha is None:
        return None
    return {"id": linha[0], "nome_arquivo": linha[1], "data_importacao": linha[2]}
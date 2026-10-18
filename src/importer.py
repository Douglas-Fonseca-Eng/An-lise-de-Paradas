"""
Importação de arquivos para o banco de dados.

Fluxo: ler o arquivo -> validar -> classificar cada registro (novo, já existe, repetido,
inválido) -> gravar só os novos em uma única transação (ou grava tudo, ou nada).
"""
import hashlib
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import insert, select

from src.leitura import ler_arquivo
from src.previa import montar_previa
from src.tabelas import arquivos_importados, paradas
from src.validacao import validar_arquivo

# Colunas do DataFrame que vão para a tabela "paradas".
COLUNAS_PARADAS = [
    "id_origem", "planta", "ct", "data_inicio", "data_fim", "quebra", "frequencia",
    "origem", "tag", "descricao_tag", "equipamento", "modo_falha", "causa_raiz", "motivo",
    "providencia", "acm", "nota_corretiva", "operador", "area_responsavel", "ultimo_usuario",
    "duracao_segundos", "duracao_minutos", "turno", "data_operacional",
    "data_inicio_reconstruida", "em_andamento", "ct_desconhecido", "possivel_duplicado",
]


def calcular_hash_conteudo(conteudo):
    """Impressão digital (SHA-256) de um conteúdo em memória. Igual à do arquivo com o mesmo conteúdo."""
    return hashlib.sha256(conteudo).hexdigest()


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


def salvar_copia(pasta, nome_arquivo, conteudo, hash_arquivo):
    """Guarda uma cópia do arquivo importado. O nome inclui parte da impressão digital, então não repete."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"{hash_arquivo[:12]}_{Path(nome_arquivo).name}"
    if not destino.exists():
        destino.write_bytes(conteudo)
    return destino


def importar_dataframe(nome_arquivo, conteudo, df_lido, engine, pasta_copia=None):
    """
    Importa para o banco um arquivo já lido. Aplica a mesma validação e a mesma classificação da
    prévia, e só grava os registros novos. Nunca sobrescreve nada. Tudo acontece em uma transação:
    se algo falhar, nada é gravado. Devolve um dicionário com o resumo do que aconteceu.
    Se pasta_copia for informada, guarda também uma cópia do arquivo original.
    """
    hash_arquivo = calcular_hash_conteudo(conteudo)

    with engine.begin() as conexao:  # transação: se algo falhar, nada é gravado
        ja_importado = conexao.execute(
            select(arquivos_importados.c.id).where(arquivos_importados.c.hash_arquivo == hash_arquivo)
        ).first()
        if ja_importado is not None:
            return {"status": "arquivo_ja_importado", "arquivo_id": ja_importado[0]}

        relatorio = validar_arquivo(df_lido)
        if relatorio["bloqueios"]:
            raise ValueError("O arquivo não pode ser importado: " + "; ".join(relatorio["bloqueios"]))

        ids_existentes = set(conexao.execute(select(paradas.c.id_origem)).scalars())
        previa = montar_previa(df_lido, relatorio, ids_existentes)
        processado = previa["processado"]
        novos = processado[processado["situacao"] == "Novo"]
        contagens = previa["contagens"]

        resumo = {
            "status": "importado",
            "total": len(processado),
            "novos": contagens["Novo"],
            "ja_existentes": contagens["Já existe no banco"],
            "repetidos_no_arquivo": contagens["Repetido no arquivo"],
            "invalidos": contagens["Inválido"],
        }

        agora = datetime.now()
        resultado = conexao.execute(insert(arquivos_importados).values(
            nome_arquivo=Path(nome_arquivo).name,
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

        registros = preparar_registros(novos, arquivo_id, agora)
        if registros:
            conexao.execute(insert(paradas), registros)

    if pasta_copia is not None:
        try:
            salvar_copia(pasta_copia, nome_arquivo, conteudo, hash_arquivo)
            resumo["copia_salva"] = True
        except OSError:
            resumo["copia_salva"] = False
    return resumo


def importar_planilha(caminho, engine):
    """Importa uma planilha Excel do disco (aba 'Paradas'). Usa as mesmas regras da importação pela interface."""
    caminho = Path(caminho)
    conteudo = caminho.read_bytes()
    df = ler_arquivo(caminho.name, conteudo, "Paradas")
    return importar_dataframe(caminho.name, conteudo, df, engine)


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
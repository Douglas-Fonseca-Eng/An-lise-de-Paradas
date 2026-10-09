"""
Definição das tabelas do banco de dados.

Escrita com SQLAlchemy "Core" para funcionar tanto em SQLite quanto,
no futuro, em PostgreSQL.
"""
from sqlalchemy import (BigInteger, Boolean, Column, Date, DateTime, Float, ForeignKey,
                        Index, Integer, MetaData, String, Table, Text, UniqueConstraint)

metadata = MetaData()

arquivos_importados = Table(
    "arquivos_importados",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("nome_arquivo", String(255), nullable=False),
    Column("hash_arquivo", String(64), nullable=False),
    Column("data_importacao", DateTime, nullable=False),
    Column("total_registros", Integer),
    Column("registros_importados", Integer),
    Column("registros_ignorados", Integer),
    Column("observacoes", Text),
    UniqueConstraint("hash_arquivo", name="uq_arquivos_hash"),
)

paradas = Table(
    "paradas",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    # Identificação e rastreabilidade
    Column("id_origem", BigInteger, nullable=False),
    Column("arquivo_id", Integer, ForeignKey("arquivos_importados.id"), nullable=False),
    Column("data_importacao", DateTime, nullable=False),
    # Dados originais
    Column("planta", String(20)),
    Column("ct", String(20), nullable=False),
    Column("data_inicio", DateTime),
    Column("data_fim", DateTime),
    Column("quebra", Integer),
    Column("frequencia", Integer),
    Column("origem", String(200)),
    Column("tag", String(50)),
    Column("descricao_tag", Text),
    Column("equipamento", String(200)),
    Column("modo_falha", String(200)),
    Column("causa_raiz", String(200)),
    Column("motivo", String(200)),
    Column("providencia", Text),
    Column("acm", String(200)),
    Column("nota_corretiva", String(200)),
    Column("operador", String(200)),
    Column("area_responsavel", String(200)),
    Column("ultimo_usuario", String(200)),
    # Campos derivados
    Column("duracao_segundos", Float),
    Column("duracao_minutos", Float),
    Column("turno", String(20)),
    Column("data_operacional", Date),
    # Avisos gerados pelo ETL
    Column("data_inicio_reconstruida", Boolean),
    Column("em_andamento", Boolean),
    Column("ct_desconhecido", Boolean),
    Column("possivel_duplicado", Boolean),
    UniqueConstraint("id_origem", name="uq_paradas_id_origem"),
    Index("ix_paradas_ct_data_inicio", "ct", "data_inicio"),
    Index("ix_paradas_data_operacional", "data_operacional"),
)
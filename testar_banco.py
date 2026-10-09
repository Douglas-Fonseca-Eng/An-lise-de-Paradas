from sqlalchemy import text

from config.settings import CAMINHO_BANCO
from src.database import obter_engine

engine = obter_engine()

with engine.connect() as conexao:
    versao = conexao.execute(text("SELECT sqlite_version()")).scalar()

print("Conexão OK. Versão do SQLite:", versao)
print("Arquivo do banco:", CAMINHO_BANCO)
print("Arquivo existe:", CAMINHO_BANCO.exists())
print("Tamanho (bytes):", CAMINHO_BANCO.stat().st_size)
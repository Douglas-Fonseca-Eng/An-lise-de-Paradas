"""
Acesso ao banco de dados.

Usamos SQLAlchemy para que, no futuro, trocar SQLite por PostgreSQL
seja basicamente mudar a URL de conexão (URL_BANCO em config/settings.py).
"""
import sqlite3
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine

from config.settings import CAMINHO_BANCO, URL_BANCO
from src.tabelas import metadata


@event.listens_for(Engine, "connect")
def _ativar_chaves_estrangeiras(conexao_dbapi, registro):
    """No SQLite, a verificação de chaves estrangeiras vem desligada. Aqui ligamos."""
    if isinstance(conexao_dbapi, sqlite3.Connection):
        cursor = conexao_dbapi.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def obter_engine(caminho=None):
    """
    Devolve o engine de conexão.
    Sem argumento, usa o banco oficial do sistema.
    Com um caminho, usa outro arquivo SQLite (útil para testes).
    """
    if caminho is None:
        # Esta linha só é necessária para SQLite (que é um arquivo).
        CAMINHO_BANCO.parent.mkdir(parents=True, exist_ok=True)
        return create_engine(URL_BANCO)

    caminho = Path(caminho).resolve()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{caminho.as_posix()}")


def criar_tabelas(engine):
    """Cria as tabelas que ainda não existem (não apaga nem altera as existentes)."""
    metadata.create_all(engine)
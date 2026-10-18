import shutil
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.database import criar_tabelas, obter_engine
from src.importer import importar_dataframe, listar_arquivos_importados
from src.leitura import ler_arquivo

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", 70)

exemplo = Path("data") / "processed" / "arquivo_exemplo.xlsx"
arquivos = sorted((Path("data") / "raw").glob("*.xlsx"))
if not arquivos or not exemplo.exists():
    raise SystemExit("Faltam a planilha em data/raw ou o arquivo_exemplo.xlsx (rode antes: python testar_previa.py).")
original = arquivos[0]

banco_teste = Path("database") / "teste.db"
pasta_copias = Path("data") / "processed" / "_copias_teste"
banco_teste.unlink(missing_ok=True)
shutil.rmtree(pasta_copias, ignore_errors=True)

engine = obter_engine(banco_teste)
criar_tabelas(engine)


def importar(caminho, titulo):
    conteudo = caminho.read_bytes()
    df = ler_arquivo(caminho.name, conteudo, "Paradas")
    resultado = importar_dataframe(caminho.name, conteudo, df, engine, pasta_copia=pasta_copias)
    print(titulo)
    print(" ", resultado)


def consultar(sql):
    with engine.connect() as conexao:
        return conexao.execute(text(sql)).fetchall()


importar(original, "1) Planilha real:")
importar(exemplo, "\n2) Arquivo de exemplo (100 já existentes, 6 novos, 1 repetido, 1 inválido):")
importar(exemplo, "\n3) O mesmo arquivo de novo:")

print("\n4) Conferência no banco de teste:")
print("  Total em paradas:", consultar("SELECT COUNT(*) FROM paradas")[0][0])
print("  Paradas do arquivo nº 2:", consultar("SELECT COUNT(*) FROM paradas WHERE arquivo_id = 2")[0][0])
print("  CTs fora da lista gravadas (ct, marca, quantidade):",
      consultar("SELECT ct, ct_desconhecido, COUNT(*) FROM paradas WHERE ct_desconhecido = 1 GROUP BY ct, ct_desconhecido"))
print("  Registro inválido (ID 2007589685) foi gravado?",
      consultar("SELECT COUNT(*) FROM paradas WHERE id_origem = 2007589685")[0][0])
print("  Cópias guardadas:", sorted(arquivo.name.split("_", 1)[1] for arquivo in pasta_copias.iterdir()))
print(listar_arquivos_importados(engine))

engine.dispose()
shutil.rmtree(pasta_copias, ignore_errors=True)
banco_teste.unlink(missing_ok=True)
print("\nBanco e cópias de teste apagados.")
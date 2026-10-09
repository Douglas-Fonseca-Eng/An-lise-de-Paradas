from pathlib import Path

from sqlalchemy import text

from src.database import criar_tabelas, obter_engine
from src.importer import importar_planilha

arquivos = sorted((Path("data") / "raw").glob("*.xlsx"))
if not arquivos:
    raise SystemExit("Nenhum .xlsx encontrado em data/raw.")

engine = obter_engine()
criar_tabelas(engine)


def consultar(sql):
    with engine.connect() as conexao:
        return conexao.execute(text(sql)).fetchall()


print("1) Primeira importação:")
print(" ", importar_planilha(arquivos[0], engine))

print("\n2) Segunda importação do mesmo arquivo:")
print(" ", importar_planilha(arquivos[0], engine))

print("\n3) Conferência no banco:")
print("  Total em paradas:", consultar("SELECT COUNT(*) FROM paradas")[0][0])
print("  Por CT:", consultar("SELECT ct, COUNT(*) FROM paradas GROUP BY ct ORDER BY ct"))
print("  Por turno:", consultar("SELECT turno, COUNT(*) FROM paradas GROUP BY turno ORDER BY turno"))
print("  Início reconstruído:",
      consultar("SELECT COUNT(*) FROM paradas WHERE data_inicio_reconstruida = 1")[0][0])
print("  Em andamento:",
      consultar("SELECT COUNT(*) FROM paradas WHERE em_andamento = 1")[0][0])
print("  Menor e maior data operacional:",
      consultar("SELECT MIN(data_operacional), MAX(data_operacional) FROM paradas")[0])
print("  Arquivos registrados:", consultar(
    "SELECT id, nome_arquivo, total_registros, registros_importados, registros_ignorados "
    "FROM arquivos_importados"))
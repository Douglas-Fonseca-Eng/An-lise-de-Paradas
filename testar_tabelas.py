from datetime import datetime

from sqlalchemy import insert, inspect, text
from sqlalchemy.exc import IntegrityError

from src.database import criar_tabelas, obter_engine
from src.tabelas import arquivos_importados, paradas

engine = obter_engine()
criar_tabelas(engine)
criar_tabelas(engine)  # segunda vez: não deve dar erro nem duplicar nada

inspetor = inspect(engine)
print("Tabelas:", sorted(inspetor.get_table_names()))

for nome in ["arquivos_importados", "paradas"]:
    colunas = inspetor.get_columns(nome)
    print(f"\n{nome}: {len(colunas)} colunas")
    for coluna in colunas:
        print(f"  {coluna['name']:<26} {coluna['type']}")

print("\nRestrições de unicidade (paradas):",
      [u["name"] for u in inspetor.get_unique_constraints("paradas")])
print("Chaves estrangeiras (paradas):",
      [(f["constrained_columns"], f["referred_table"]) for f in inspetor.get_foreign_keys("paradas")])
print("Índices (paradas):", sorted(i["name"] for i in inspetor.get_indexes("paradas")))

print("\nTeste de duplicidade (tudo é desfeito no final):")
with engine.connect() as conexao:
    resultado = conexao.execute(insert(arquivos_importados).values(
        nome_arquivo="teste.xlsx", hash_arquivo="teste", data_importacao=datetime.now()))
    id_arquivo = resultado.inserted_primary_key[0]

    linha = dict(id_origem=1, arquivo_id=id_arquivo, data_importacao=datetime.now(), ct="SBL-P2")
    conexao.execute(insert(paradas).values(**linha))
    try:
        conexao.execute(insert(paradas).values(**linha))
        print("  ERRO: o banco aceitou o id_origem repetido")
    except IntegrityError:
        print("  O banco recusou o id_origem repetido (correto).")
    conexao.rollback()

with engine.connect() as conexao:
    total = conexao.execute(text("SELECT COUNT(*) FROM paradas")).scalar()
print("  Registros em paradas depois do teste:", total)
import shutil
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.database import criar_tabelas, obter_engine
from src.importer import importar_planilha, listar_arquivos_importados

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", 70)

arquivos = sorted((Path("data") / "raw").glob("*.xlsx"))
if not arquivos:
    raise SystemExit("Nenhum .xlsx encontrado em data/raw.")
original = arquivos[0]

pasta_teste = Path("data") / "processed" / "_teste_controle"
banco_teste = Path("database") / "teste.db"

# Começa sempre do zero, só com arquivos e banco de teste (o banco oficial não é tocado).
shutil.rmtree(pasta_teste, ignore_errors=True)
banco_teste.unlink(missing_ok=True)
pasta_teste.mkdir(parents=True)

# Arquivo 2: cópia idêntica, com outro nome.
copia = pasta_teste / "copia_renomeada.xlsx"
shutil.copy(original, copia)

# Arquivo 3: 100 paradas antigas + 5 novas + 1 repetida + 1 inválida (sem CT).
base = pd.read_excel(original, sheet_name="Paradas")
antigas = base.iloc[:100]
novas = base.iloc[100:105].copy()
novas["ID"] = novas["ID"] + 1_000_000_000
repetida = base.iloc[[0]]
invalida = base.iloc[[1]].copy()
invalida["ID"] = invalida["ID"] + 2_000_000_000
invalida["CT"] = None

arquivo_b = pd.concat([antigas, novas, repetida, invalida], ignore_index=True)
# O Pandas arredonda durações para dias ao gravar no Excel; aqui gravamos como texto.
arquivo_b["Duração"] = arquivo_b["Duração"].astype(str)
caminho_b = pasta_teste / "arquivo_b.xlsx"
arquivo_b.to_excel(caminho_b, sheet_name="Paradas", index=False)

engine = obter_engine(banco_teste)
criar_tabelas(engine)


def contar_paradas(motor):
    with motor.connect() as conexao:
        return conexao.execute(text("SELECT COUNT(*) FROM paradas")).scalar()


print("1) Arquivo original:")
print(" ", importar_planilha(original, engine))

print("\n2) Mesma planilha com outro nome:")
print(" ", importar_planilha(copia, engine))

print("\n3) Arquivo B (100 antigas + 5 novas + 1 repetida + 1 inválida):")
print(" ", importar_planilha(caminho_b, engine))

print("\n4) Histórico de importações:")
print(listar_arquivos_importados(engine))

print("\n5) Totais:")
print("  Banco de teste:", contar_paradas(engine))
print("  Banco oficial (não deve ter mudado):", contar_paradas(obter_engine()))

# Limpeza: apaga os arquivos e o banco de teste.
engine.dispose()
shutil.rmtree(pasta_teste, ignore_errors=True)
banco_teste.unlink(missing_ok=True)
print("\nArquivos e banco de teste apagados.")
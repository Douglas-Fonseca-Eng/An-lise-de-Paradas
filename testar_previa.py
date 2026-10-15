import datetime
from pathlib import Path

import pandas as pd

from src.leitura import ler_arquivo
from src.previa import montar_previa, problemas_por_linha
from src.validacao import validar_arquivo

pd.set_option("display.width", 200)

arquivos = sorted((Path("data") / "raw").glob("*.xlsx"))
if not arquivos:
    raise SystemExit("Nenhum .xlsx encontrado em data/raw.")
original = arquivos[0]
base = ler_arquivo(original.name, original.read_bytes(), "Paradas")

# Os IDs da planilha real fazem o papel do banco (que já a contém).
ids_no_banco = set(pd.to_numeric(base["ID"]).astype(int))

# Arquivo de exemplo: 100 paradas que já existem, 6 novas, 1 repetida e 1 inválida.
antigas = base.iloc[:100]
novas = base.iloc[100:106].copy()
novas["ID"] = novas["ID"] + 1_000_000_000
novas["CT"] = novas["CT"].astype(object)
novas.iloc[5, novas.columns.get_loc("CT")] = "p4"                 # nova, mas com CT fora da lista
repetida = base.iloc[[0]]
invalida = base.iloc[[1]].copy()
invalida["ID"] = invalida["ID"] + 2_000_000_000
invalida["CT"] = invalida["CT"].astype(object)
invalida["CT"] = None                                             # inválida: sem CT

exemplo = pd.concat([antigas, novas, repetida, invalida], ignore_index=True)
exemplo["Duração"] = exemplo["Duração"].astype(str)               # o Excel do Pandas arredonda durações
caminho = Path("data") / "processed" / "arquivo_exemplo.xlsx"
exemplo.to_excel(caminho, sheet_name="Paradas", index=False)


def mostrar(titulo, df, ids):
    relatorio = validar_arquivo(df)
    previa = montar_previa(df, relatorio, ids)
    print(titulo)
    print("  Contagens:", previa["contagens"])
    print("  Período dos novos:", previa["periodo"])
    print("  Horas dos novos:", round(previa["horas_novas"], 1))
    if not previa["por_ct"].empty:
        print(previa["por_ct"].round(2).to_string(index=False))
    return relatorio, previa


print("1) Arquivo real, com o banco já contendo todos os seus IDs:")
mostrar("", base, ids_no_banco)

print("\n2) Arquivo real, com o banco vazio:")
mostrar("", base, set())

print(f"\n3) {caminho.name}, com o banco contendo a planilha real:")
lido = ler_arquivo(caminho.name, caminho.read_bytes(), "Paradas")
relatorio, previa = mostrar("", lido, ids_no_banco)
processado = previa["processado"]
mostrar_colunas = ["linha_arquivo", "id_origem", "ct", "situacao"]
print(processado.loc[processado["situacao"] != "Já existe no banco", mostrar_colunas].to_string(index=False))
print("  Problemas por linha:", problemas_por_linha(relatorio))
print("  CTs fora da lista:", relatorio["ct_desconhecidas"])

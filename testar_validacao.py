import datetime
from pathlib import Path

import pandas as pd

from src.leitura import ler_arquivo
from src.validacao import validar_arquivo

pd.set_option("display.width", 200)

arquivos = sorted((Path("data") / "raw").glob("*.xlsx"))
if not arquivos:
    raise SystemExit("Nenhum .xlsx encontrado em data/raw.")
original = arquivos[0]
base = ler_arquivo(original.name, original.read_bytes(), "Paradas")


def mostrar(relatorio):
    print("  Bloqueios:", relatorio["bloqueios"] or "nenhum")
    print("  Total:", relatorio["total"], "| válidos:", relatorio["validos"],
          "| inválidos:", relatorio["linhas_invalidas"], "| repetidos:", relatorio["linhas_repetidas"])
    print("  Colunas desconhecidas:", relatorio["colunas"]["desconhecidas"] or "nenhuma")
    print("  CTs fora da lista:", relatorio["ct_desconhecidas"] or "nenhuma")
    for nome, quantidade in relatorio["avisos"].items():
        if quantidade:
            print(f"  Aviso - {nome}: {quantidade}")
    if relatorio["linhas_invalidas"]:
        print(relatorio["invalidos"].to_string(index=False))
    if relatorio["linhas_repetidas"]:
        print(relatorio["repetidos"].to_string(index=False))


print("1) Arquivo real:")
mostrar(validar_arquivo(base))

# Arquivo de 12 linhas com problemas de propósito, gravado e lido de volta, como no upload.
ruim = base.iloc[:12].copy().reset_index(drop=True)
for coluna in ["ID", "Duração", "CT", "Data Inicio", "Data Fim"]:
    ruim[coluna] = ruim[coluna].astype(object)
ruim.loc[0, "ID"] = "abc"                                  # linha 2: ID inválido
ruim.loc[1, "CT"] = None                                   # linha 3: sem CT
ruim.loc[2, "Duração"] = pd.Timedelta(minutes=-5)          # linha 4: duração negativa
ruim.loc[3, "Data Fim"] = datetime.datetime(2026, 8, 1)    # linha 5: fim antes do início
ruim.loc[4, "Data Inicio"] = "31/02/2026"                  # linha 6: data impossível
ruim.loc[5, "Duração"] = "xyz"                             # linha 7: duração ilegível
ruim.loc[6, "ID"] = ruim.loc[7, "ID"]                      # linha 9: ID repetido
ruim.loc[8, "CT"] = "p4"                                   # linha 10: CT fora da lista
ruim.loc[9, "Data Inicio"] = None                          # linha 11: sem início e sem fim
ruim.loc[9, "Data Fim"] = None
ruim["Coluna Estranha"] = 1
ruim["Duração"] = ruim["Duração"].astype(str)              # o Excel do Pandas arredonda durações

caminho = Path("data") / "processed" / "arquivo_com_problemas.xlsx"
ruim.to_excel(caminho, sheet_name="Paradas", index=False)

print("\n2) Arquivo com problemas (" + caminho.name + "):")
lido = ler_arquivo(caminho.name, caminho.read_bytes(), "Paradas")
mostrar(validar_arquivo(lido))

print("\n3) Arquivo sem as colunas ID e Duração:")
mostrar(validar_arquivo(base.drop(columns=["ID", "Duração"])))
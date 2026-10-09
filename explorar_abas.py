from pathlib import Path
import pandas as pd

pasta_raw = Path("data") / "raw"
arquivos = sorted(pasta_raw.glob("*.xlsx"))

if not arquivos:
    raise SystemExit("Nenhum .xlsx encontrado em data/raw.")

caminho = arquivos[0]
print("Arquivo:", caminho.name)

excel = pd.ExcelFile(caminho)
print("\nNúmero de abas:", len(excel.sheet_names))

for nome_aba in excel.sheet_names:
    df_aba = excel.parse(nome_aba)
    print(f"\nAba: {nome_aba!r}")
    print("  Linhas:", df_aba.shape[0])
    print("  Colunas:", df_aba.shape[1])
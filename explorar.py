from pathlib import Path
import pandas as pd

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)

pasta_raw = Path("data") / "raw"
arquivos = sorted(pasta_raw.glob("*.xlsx"))

print("Arquivos .xlsx encontrados em data/raw:")
for arquivo in arquivos:
    print(" -", arquivo.name)

if not arquivos:
    raise SystemExit("Nenhum .xlsx encontrado em data/raw. Copie a planilha para lá.")

caminho = arquivos[0]
print("\nLendo:", caminho.name)

df = pd.read_excel(caminho)

print("\nLinhas:", df.shape[0])
print("Colunas:", df.shape[1])
print("\nPrimeiras 5 linhas:")
print(df.head())
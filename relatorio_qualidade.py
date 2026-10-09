from pathlib import Path
import pandas as pd

pasta_raw = Path("data") / "raw"
arquivos = sorted(pasta_raw.glob("*.xlsx"))

if not arquivos:
    raise SystemExit("Nenhum .xlsx encontrado em data/raw.")

caminho = arquivos[0]
df = pd.read_excel(caminho, sheet_name="Paradas")

print("Arquivo:", caminho.name)
print("Total de registros:", len(df))

print("\n1) Registros por CT:")
print(df["CT"].value_counts())

print("\n2) Duplicidades:")
print("  IDs repetidos:", df["ID"].duplicated().sum())
print("  Linhas totalmente idênticas:", df.duplicated().sum())

inicio = pd.to_datetime(df["Data Inicio"], format="mixed", errors="coerce")
fim = pd.to_datetime(df["Data Fim"], format="mixed", errors="coerce")

print("\n3) Datas:")
print("  Data Inicio que não virou data:", inicio.isna().sum())
print("  Data Fim que não virou data:", fim.isna().sum())
print("  Menor data de início:", inicio.min())
print("  Maior data de fim:", fim.max())

print("\n4) Durações:")
print("  Duração negativa:", (df["Duração Decimal"] < 0).sum())
print("  Duração zero:", (df["Duração Decimal"] == 0).sum())
print("  Data Fim anterior à Data Inicio:", (fim < inicio).sum())

print("\n5) Células que contêm apenas '-' (por coluna):")
total_traco = 0
for coluna in df.columns:
    qtd = (df[coluna].astype(str).str.strip() == "-").sum()
    if qtd > 0:
        print(f"  {coluna}: {qtd}")
        total_traco += qtd
if total_traco == 0:
    print("  Nenhuma")
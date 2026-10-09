from pathlib import Path
import pandas as pd

from config.schema import COLUNAS

pasta_raw = Path("data") / "raw"
arquivos = sorted(pasta_raw.glob("*.xlsx"))

if not arquivos:
    raise SystemExit("Nenhum .xlsx encontrado em data/raw.")

caminho = arquivos[0]
df = pd.read_excel(caminho, sheet_name="Paradas")

nomes_planilha = list(df.columns)
nomes_schema = [c["original"] for c in COLUNAS]

print("Arquivo:", caminho.name)
print("Colunas no schema:", len(nomes_schema))
print("Colunas na planilha:", len(nomes_planilha))

faltando = [n for n in nomes_schema if n not in nomes_planilha]
sobrando = [n for n in nomes_planilha if n not in nomes_schema]
obrigatorias_faltando = [c["original"] for c in COLUNAS if c["obrigatoria"] and c["original"] not in nomes_planilha]

print("\nNo schema, mas ausentes na planilha:", faltando if faltando else "nenhuma")
print("Na planilha, mas fora do schema:", sobrando if sobrando else "nenhuma")
print("Obrigatórias ausentes:", obrigatorias_faltando if obrigatorias_faltando else "nenhuma")

print("\nMapeamento original -> interno:")
for c in COLUNAS:
    marca = "*" if c["obrigatoria"] else " "
    print(f"  {marca} {c['original']:<20} -> {c['interno']}")
print("\n(* = obrigatória)")
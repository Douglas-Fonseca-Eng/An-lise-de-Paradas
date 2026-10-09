from pathlib import Path
import pandas as pd

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 220)
pd.set_option("display.max_colwidth", 30)

pasta_raw = Path("data") / "raw"
arquivos = sorted(pasta_raw.glob("*.xlsx"))

if not arquivos:
    raise SystemExit("Nenhum .xlsx encontrado em data/raw.")

caminho = arquivos[0]

print("Arquivo:", caminho.name)

df = pd.read_excel(caminho, sheet_name="Paradas")
print("Linhas:", df.shape[0], "| Colunas:", df.shape[1])

print("\nNomes exatos das colunas (entre aspas, para ver espaços escondidos):")
for posicao, nome in enumerate(df.columns):
    print(f"  {posicao:2d}  {nome!r}")

resumo = pd.DataFrame({
    "tipo": df.dtypes.astype(str),
    "preenchidos": df.notna().sum(),
    "vazios": df.isna().sum(),
    "%_vazio": (df.isna().mean() * 100).round(1),
    "valores_unicos": df.nunique(),
    "exemplo": df.apply(lambda col: col.dropna().iloc[0] if col.notna().any() else None),
})

print("\nResumo por coluna:")
print(resumo)
resumo["exemplo"] = resumo["exemplo"].astype(str)

saida = Path("data") / "processed" / "resumo_colunas.xlsx"
resumo.to_excel(saida, index_label="coluna")
print("\nResumo salvo em:", saida)
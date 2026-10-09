from pathlib import Path
import pandas as pd

from src.transformer import limpar_texto, padronizar_ct, renomear_colunas

arquivos = sorted((Path("data") / "raw").glob("*.xlsx"))
if not arquivos:
    raise SystemExit("Nenhum .xlsx encontrado em data/raw.")

df = pd.read_excel(arquivos[0], sheet_name="Paradas")
df, _ = renomear_colunas(df)


def contar_espaco_duplo(tabela, coluna):
    return tabela[coluna].dropna().astype(str).str.contains(r"\s{2,}").sum()


print("1) Limpeza de texto (espaços duplicados):")
for coluna in ["descricao_tag", "providencia"]:
    antes = contar_espaco_duplo(df, coluna)
    depois = contar_espaco_duplo(limpar_texto(df), coluna)
    print(f"  {coluna}: antes={antes} | depois={depois}")

df = limpar_texto(df)
df = padronizar_ct(df)

print("\n2) CTs na planilha real:")
print(df["ct"].value_counts())
print("  CTs desconhecidos:", df["ct_desconhecido"].sum())

print("\n3) Teste com CTs de mentira:")
falso = pd.DataFrame({"ct": ["sbl-p4", "  SBL-P2 ", "P4", None]})
resultado = padronizar_ct(falso)
print(resultado)
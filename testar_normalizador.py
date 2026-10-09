from pathlib import Path
import pandas as pd

from src.transformer import MAPA_NOMES, normalizar_nome, renomear_colunas

print("1) Nomes alternativos -> nome interno:")
for nome in ["Data Inicio", "Data Início", "DataInicio", "data_inicio", "DATA  INICIO"]:
    print(f"  {nome!r:<16} -> {MAPA_NOMES.get(normalizar_nome(nome))}")

print("\n2) Planilha real:")
arquivos = sorted((Path("data") / "raw").glob("*.xlsx"))
if not arquivos:
    raise SystemExit("Nenhum .xlsx encontrado em data/raw.")

df = pd.read_excel(arquivos[0], sheet_name="Paradas")
df_novo, rel = renomear_colunas(df)
print("  Colunas renomeadas:", len(rel["renomeadas"]))
print("  Desconhecidas:", rel["desconhecidas"] or "nenhuma")
print("  Obrigatórias ausentes:", rel["obrigatorias_ausentes"] or "nenhuma")
print("  Novos nomes:", list(df_novo.columns))

print("\n3) Arquivo de mentira, com colunas faltando:")
falso = pd.DataFrame({"CT": ["SBL-P2"], "DataInicio": ["x"], "Coluna Estranha": [1]})
_, rel = renomear_colunas(falso)
print("  Renomeadas:", rel["renomeadas"])
print("  Desconhecidas:", rel["desconhecidas"] or "nenhuma")
print("  Obrigatórias ausentes:", rel["obrigatorias_ausentes"] or "nenhuma")
from pathlib import Path

import pandas as pd

arquivos = sorted((Path("data") / "raw").glob("*.xlsx"))
if not arquivos:
    raise SystemExit("Nenhum .xlsx encontrado em data/raw.")

base = pd.read_excel(arquivos[0], sheet_name="Paradas")

# 300 paradas do meio do mês, deslocadas 30 dias para a frente, com IDs novos.
novo = base.iloc[4000:4300].copy().reset_index(drop=True)
novo["ID"] = novo["ID"] + 3_000_000_000
deslocamento = pd.Timedelta(days=30)
for coluna in ["Data Inicio", "Data Fim"]:
    novo[coluna] = pd.to_datetime(novo[coluna]) + deslocamento
novo["Duração"] = novo["Duração"].astype(str)  # o Excel do Pandas arredonda durações

caminho = Path("data") / "processed" / "arquivo_mes_seguinte.xlsx"
novo.to_excel(caminho, sheet_name="Paradas", index=False)

print("Arquivo criado:", caminho)
print("Linhas:", len(novo))
print("Primeiro início:", novo["Data Inicio"].min(), "| último fim:", novo["Data Fim"].max())
print("Paradas por CT:", novo["CT"].value_counts().sort_index().to_dict())
print("Duração total (horas):", round(novo["Duração Decimal"].sum(), 1))
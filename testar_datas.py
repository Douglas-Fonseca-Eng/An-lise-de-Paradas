from pathlib import Path
import pandas as pd

from src.transformer import padronizar_datas, padronizar_duracao, renomear_colunas

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", None)

arquivos = sorted((Path("data") / "raw").glob("*.xlsx"))
if not arquivos:
    raise SystemExit("Nenhum .xlsx encontrado em data/raw.")

df = pd.read_excel(arquivos[0], sheet_name="Paradas")
df, _ = renomear_colunas(df)
df = padronizar_duracao(df)
df = padronizar_datas(df)

print("Registros:", len(df))

print("\n1) Datas:")
print("  Tipo de data_inicio:", df["data_inicio"].dtype)
print("  Tipo de data_fim:", df["data_fim"].dtype)
print("  Início reconstruído (regra B):", df["data_inicio_reconstruida"].sum())
print("  Em andamento (regra C):", df["em_andamento"].sum())
print("  data_inicio vazia:", df["data_inicio"].isna().sum())
print("  data_fim vazia:", df["data_fim"].isna().sum())
print("  Menor data_inicio:", df["data_inicio"].min())
print("  Maior data_fim:", df["data_fim"].max())

print("\n2) Registros tratados:")
tratados = df[df["data_inicio_reconstruida"] | df["em_andamento"]]
print(tratados[["id_origem", "ct", "data_inicio", "data_fim", "duracao_minutos",
                "data_inicio_reconstruida", "em_andamento"]])

print("\n3) Duração:")
print("  Mediana (minutos):", round(df["duracao_minutos"].median(), 2))
print("  Maior (minutos):", round(df["duracao_minutos"].max(), 2))
diferenca = (df["duracao_segundos"] / 3600 - df["duracao_decimal_horas"]).abs().max()
print("  Maior diferença para duracao_decimal_horas (horas):", round(diferenca, 6))
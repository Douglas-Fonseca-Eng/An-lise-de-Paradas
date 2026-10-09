from pathlib import Path
import pandas as pd

from src.transformer import (atribuir_turno, criar_features_basicas, padronizar_ct,
                             padronizar_datas, padronizar_duracao, renomear_colunas)

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", None)

print("1) Teste com dados de mentira:")
falso = pd.DataFrame({
    "ct": ["SBL-P2", "SBL-P2", "SBL-P2", "SBL-P4"],
    "data_inicio": pd.to_datetime(["2026-09-01 10:00:00", "2026-09-01 10:05:00",
                                   "2026-09-01 10:30:00", "2026-09-01 10:02:00"]),
    "data_fim": pd.to_datetime(["2026-09-01 10:01:00", "2026-09-01 10:10:00",
                                "2026-09-01 11:45:00", "2026-09-01 10:03:00"]),
    "duracao_minutos": [1.0, 5.0, 75.0, 1.5],
})
print(criar_features_basicas(falso)[["ct", "data_inicio", "hora_inicio", "dia_semana",
                                     "duracao_minutos", "microparada", "faixa_duracao",
                                     "intervalo_anterior_min"]])

print("\n2) Planilha real:")
arquivos = sorted((Path("data") / "raw").glob("*.xlsx"))
if not arquivos:
    raise SystemExit("Nenhum .xlsx encontrado em data/raw.")

df = pd.read_excel(arquivos[0], sheet_name="Paradas")
df, _ = renomear_colunas(df)
df = padronizar_duracao(df)
df = padronizar_datas(df)
df = padronizar_ct(df)
df = atribuir_turno(df)
df = criar_features_basicas(df)

print("  Microparadas:", df["microparada"].sum())
print("  hora_inicio vai de", df["hora_inicio"].min(), "a", df["hora_inicio"].max())
print("  dia_semana vai de", df["dia_semana"].min(), "a", df["dia_semana"].max())
print("  intervalo_anterior_min vazio:", df["intervalo_anterior_min"].isna().sum())
print("  intervalo_anterior_min negativo:", (df["intervalo_anterior_min"] < 0).sum())
print("  Mediana do intervalo (min):", round(df["intervalo_anterior_min"].median(), 2))

print("\n3) Paradas por faixa de duração:")
print(df["faixa_duracao"].value_counts(sort=False))

print("\n4) Microparadas por CT:")
print(df.groupby("ct")["microparada"].agg(["sum", "count"]))
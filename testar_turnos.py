from pathlib import Path
import pandas as pd

from config.shifts import TURNOS
from src.transformer import (atribuir_turno, padronizar_ct, padronizar_datas,
                             padronizar_duracao, renomear_colunas)

pd.set_option("display.width", 200)

print("1) Teste nas fronteiras dos turnos:")
horarios = [
    "2026-09-10 05:29:59", "2026-09-10 05:30:00", "2026-09-10 14:29:59",
    "2026-09-10 14:30:00", "2026-09-10 22:29:59", "2026-09-10 22:30:00",
    "2026-09-10 23:59:59", "2026-09-11 00:00:00", "2026-09-11 02:30:00",
]
falso = pd.DataFrame({"data_inicio": pd.to_datetime(horarios + [None])})
resultado = atribuir_turno(falso)
resultado["data_operacional"] = resultado["data_operacional"].dt.date
print(resultado)

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

print("  Registros sem turno:", df["turno"].isna().sum())
print("  Menor data_operacional:", df["data_operacional"].min().date())
print("  Maior data_operacional:", df["data_operacional"].max().date())

print("\n  Paradas e tempo parado por turno:")
resumo = df.groupby("turno").agg(
    paradas=("id_origem", "count"),
    horas_paradas=("duracao_segundos", lambda s: round(s.sum() / 3600, 1)),
)
print(resumo)

print("\n3) Duração de cada turno (horas):")
for t in TURNOS:
    ini = t["inicio"].hour * 60 + t["inicio"].minute
    fim = t["fim"].hour * 60 + t["fim"].minute
    horas = ((fim - ini) % (24 * 60)) / 60
    print(f"  Turno {t['nome']}: {horas:.0f} h")
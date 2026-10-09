from pathlib import Path
import pandas as pd

from src.transformer import (limpar_texto, marcar_duplicados, padronizar_ct,
                             padronizar_datas, padronizar_duracao,
                             renomear_colunas, tratar_ausentes)

pd.set_option("display.width", 200)

arquivos = sorted((Path("data") / "raw").glob("*.xlsx"))
if not arquivos:
    raise SystemExit("Nenhum .xlsx encontrado em data/raw.")

df = pd.read_excel(arquivos[0], sheet_name="Paradas")
df, _ = renomear_colunas(df)
df = padronizar_duracao(df)
df = padronizar_datas(df)
df = limpar_texto(df)
df = padronizar_ct(df)
df = tratar_ausentes(df)
df = marcar_duplicados(df)

print("1) Planilha real:")
print("  Registros:", len(df))
print("  duplicado_id:", df["duplicado_id"].sum())
print("  possivel_duplicado:", df["possivel_duplicado"].sum())

print("\n2) Teste com dados de mentira:")
falso = pd.DataFrame({
    "id_origem": [1, 2, 1, 3, 4, 5, 6],
    "ct": ["SBL-P2", "SBL-P2", "SBL-P2", "SBL-P2", "SBL-P4", "SBL-P4", "SBL-P4"],
    "data_inicio": pd.to_datetime([
        "2026-09-01 10:00", "2026-09-01 11:00", "2026-09-01 12:00",
        "2026-09-01 11:00", "2026-09-01 11:00", None, None,
    ]),
})
print(marcar_duplicados(falso))
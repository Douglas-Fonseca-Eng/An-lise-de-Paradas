from pathlib import Path
import pandas as pd

from config.schema import COLUNAS_COM_MARCADOR_VAZIO, MARCADORES_VAZIO
from src.transformer import (limpar_texto, padronizar_ct, padronizar_datas,
                             padronizar_duracao, renomear_colunas, tratar_ausentes)

pd.set_option("display.max_rows", None)

arquivos = sorted((Path("data") / "raw").glob("*.xlsx"))
if not arquivos:
    raise SystemExit("Nenhum .xlsx encontrado em data/raw.")

df = pd.read_excel(arquivos[0], sheet_name="Paradas")
df, _ = renomear_colunas(df)
df = padronizar_duracao(df)
df = padronizar_datas(df)
df = limpar_texto(df)
df = padronizar_ct(df)

print("1) Marcador '-' antes -> ausentes depois (regra A):")
tratado = tratar_ausentes(df)
for coluna in COLUNAS_COM_MARCADOR_VAZIO:
    antes = df[coluna].astype(str).str.strip().isin(MARCADORES_VAZIO).sum()
    depois = tratado[coluna].isna().sum()
    print(f"  {coluna:<16} '-' antes={antes:<5} | ausentes depois={depois}")

print("\n2) Tipo de 'frequencia' depois:", tratado["frequencia"].dtype)

print("\n3) Registros sem motivo e sem origem ao mesmo tempo:",
      (tratado["motivo"].isna() & tratado["origem"].isna()).sum())

print("\n4) Valores ausentes por coluna (depois do tratamento):")
resumo = pd.DataFrame({
    "ausentes": tratado.isna().sum(),
    "%": (tratado.isna().mean() * 100).round(1),
})
print(resumo[resumo["ausentes"] > 0].sort_values("%", ascending=False))
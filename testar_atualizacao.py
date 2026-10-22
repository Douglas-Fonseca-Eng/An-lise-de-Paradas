import shutil
from pathlib import Path

from src.analytics import carregar_paradas, obter_versao_dados
from src.database import criar_tabelas, obter_engine
from src.importer import importar_dataframe
from src.leitura import ler_arquivo

novo = Path("data") / "processed" / "arquivo_mes_seguinte.xlsx"
arquivos = sorted((Path("data") / "raw").glob("*.xlsx"))
if not arquivos or not novo.exists():
    raise SystemExit("Faltam a planilha em data/raw ou o arquivo_mes_seguinte.xlsx (rode antes: python criar_arquivo_novo_mes.py).")
original = arquivos[0]

banco_teste = Path("database") / "teste.db"
banco_teste.unlink(missing_ok=True)

engine = obter_engine(banco_teste)
criar_tabelas(engine)


def importar(caminho):
    conteudo = caminho.read_bytes()
    df = ler_arquivo(caminho.name, conteudo, "Paradas")
    return importar_dataframe(caminho.name, conteudo, df, engine)


def situacao(titulo):
    df = carregar_paradas(engine)
    primeira = df["data_inicio"].min().strftime("%d/%m/%Y")
    ultima = df["data_inicio"].max().strftime("%d/%m/%Y")
    print(f"{titulo}: versão = {obter_versao_dados(engine)} | paradas = {len(df)} | "
          f"primeira parada = {primeira} | última = {ultima}")
    return df


print("Antes de importar nada: versão dos dados =", obter_versao_dados(engine))

importar(original)
situacao("Depois da planilha real")

print("Importando o arquivo do mês seguinte:", importar(novo))
df = situacao("Depois do arquivo do mês seguinte")

print("Paradas por CT:", df["ct"].value_counts().sort_index().to_dict())
print("Horas paradas:", round(df["duracao_minutos"].sum() / 60, 1))

primeira_nova = df[df["id_origem"] == 3007628921].iloc[0]
print("Primeira parada nova (ID 3007628921): intervalo desde a parada anterior da mesma CT =",
      round(primeira_nova["intervalo_anterior_min"], 1), "min")

engine.dispose()
banco_teste.unlink(missing_ok=True)
print("Banco de teste apagado.")
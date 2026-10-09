"""
Funções pequenas de formatação, no padrão brasileiro, usadas pelo dashboard.
"""
import pandas as pd


def formatar_inteiro(valor):
    """9039 -> '9.039'"""
    return f"{int(valor):,}".replace(",", ".")


def formatar_data(valor):
    """Timestamp -> '01/09/2026'. Valor ausente vira '-'."""
    if valor is None or pd.isna(valor):
        return "-"
    return valor.strftime("%d/%m/%Y")


def resumo_dados(df, historico):
    """Linhas de texto com o estado dos dados, para a barra lateral."""
    if df.empty:
        return ["Banco de dados vazio."]

    linhas = [
        f"{formatar_inteiro(len(df))} paradas",
        f"Período: {formatar_data(df['data_inicio'].min())} a {formatar_data(df['data_inicio'].max())}",
    ]
    if not historico.empty:
        ultimo = historico.iloc[0]
        linhas.append(f"Última importação: {ultimo['data_importacao'].strftime('%d/%m/%Y %H:%M')}")
        linhas.append(f"Arquivo: {ultimo['nome_arquivo']}")
    return linhas


def formatar_decimal(valor, casas=1):
    """1234.5 -> '1.234,5'"""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "#").replace(".", ",").replace("#", ".")


def formatar_percentual(parte, total):
    """(3545, 9039) -> '39,2%'. Total zero vira '-'."""
    if not total:
        return "-"
    return f"{formatar_decimal(parte / total * 100, 1)}%"


def formatar_horas(minutos):
    """131112 -> '2.185,2 h'"""
    if minutos is None or pd.isna(minutos):
        return "-"
    return f"{formatar_decimal(minutos / 60, 1)} h"


def formatar_minutos(minutos):
    """Converte minutos em texto legível: 45 s, 1,6 min, 45 min, 1 h 05 min, 2 d 3 h 10 min."""
    if minutos is None or pd.isna(minutos):
        return "-"
    if minutos < 1:
        return f"{round(minutos * 60)} s"
    if minutos < 10:
        return f"{minutos:.1f}".replace(".", ",") + " min"
    total = int(round(minutos))
    dias, resto = divmod(total, 1440)
    horas, mins = divmod(resto, 60)
    if dias:
        return f"{dias} d {horas} h {mins:02d} min"
    if horas:
        return f"{horas} h {mins:02d} min"
    return f"{mins} min"


def rotulo_limite(minutos):
    """5 -> '5 min'; 60 -> '1 h'; 90 -> '90 min'."""
    if minutos % 60 == 0:
        return f"{int(minutos // 60)} h"
    return f"{minutos:g} min"


def _texto(valor):
    """Valor ausente vira '—'; o resto vira texto."""
    return "—" if valor is None or pd.isna(valor) else str(valor)


def _data_hora(valor):
    return "—" if valor is None or pd.isna(valor) else valor.strftime("%d/%m/%Y %H:%M:%S")


def detalhes_da_parada(parada):
    """
    Organiza os campos de uma parada (uma linha do DataFrame) em dois grupos de pares
    (rótulo, valor) já formatados, para a tela de detalhes.
    """
    inicio = _data_hora(parada["data_inicio"])
    if parada["data_inicio_reconstruida"]:
        inicio += " (reconstruído a partir do fim e da duração)"
    fim = "em andamento" if parada["em_andamento"] else _data_hora(parada["data_fim"])
    quebra = {1: "Sim", 0: "Não"}.get(parada["quebra"], "—") if not pd.isna(parada["quebra"]) else "—"

    quando = [
        ("Início", inicio),
        ("Fim", fim),
        ("Duração", formatar_minutos(parada["duracao_minutos"])),
        ("Faixa de duração", _texto(parada["faixa_duracao"])),
        ("Turno", _texto(parada["turno"])),
        ("Data operacional", "—" if pd.isna(parada["data_operacional"]) else parada["data_operacional"].strftime("%d/%m/%Y")),
        ("Intervalo desde a parada anterior", formatar_minutos(parada["intervalo_anterior_min"])),
    ]
    o_que = [
        ("CT", _texto(parada["ct"])),
        ("Motivo", _texto(parada["motivo"])),
        ("Origem", _texto(parada["origem"])),
        ("Tag", _texto(parada["tag"])),
        ("Descrição da tag", _texto(parada["descricao_tag"])),
        ("Operador", _texto(parada["operador"])),
        ("Área responsável", _texto(parada["area_responsavel"])),
        ("Providência", _texto(parada["providencia"])),
        ("Quebra", quebra),
    ]
    return quando, o_que
"""
Gráficos Plotly do dashboard. Cada função recebe dados já resumidos e devolve uma figura.
"""
import plotly.graph_objects as go

from config.theme import AZUL_ESCURO, CINZA, CINZA_ESCURO, SEQUENCIA_CATEGORIAS
from src.utils import formatar_decimal

def grafico_participacao(resumo, rotulo_grupo):
    """Barras lado a lado: % das paradas (quantidade) x % do tempo parado, por grupo."""
    dados_hover = resumo[["paradas", "tempo_horas"]].to_numpy()
    hover = (
        "<b>%{x}</b><br>Participação: %{y:.1f}%"
        "<br>Paradas: %{customdata[0]:,.0f}"
        "<br>Tempo parado: %{customdata[1]:,.1f} h<extra></extra>"
    )

    figura = go.Figure()
    figura.add_bar(
        x=resumo["grupo"], y=resumo["pct_paradas"], name="% das paradas (quantidade)",
        marker_color=CINZA, text=[f"{v:.1f}%" for v in resumo["pct_paradas"]],
        textposition="outside", cliponaxis=False, customdata=dados_hover, hovertemplate=hover,
    )
    figura.add_bar(
        x=resumo["grupo"], y=resumo["pct_tempo"], name="% do tempo parado",
        marker_color=AZUL_ESCURO, text=[f"{v:.1f}%" for v in resumo["pct_tempo"]],
        textposition="outside", cliponaxis=False, customdata=dados_hover, hovertemplate=hover,
    )

    topo = max(resumo["pct_paradas"].max(), resumo["pct_tempo"].max())
    figura.update_layout(
        barmode="group",
        bargap=0.25,
        template="plotly_white",
        height=420,
        margin=dict(t=60, b=40, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(type="category", title=rotulo_grupo),
        yaxis=dict(ticksuffix="%", range=[0, topo * 1.18], title=None),
        font=dict(color=CINZA_ESCURO),
    )
    return figura


def grafico_serie_temporal(serie, coluna, titulo_eixo, formato_eixo="%d/%m", formato_hover="%d/%m/%Y"):
    """Linhas ao longo do tempo, uma por grupo (ou uma só, 'Total')."""
    figura = go.Figure()
    grupos = list(dict.fromkeys(serie["grupo"]))
    casas = 0 if coluna == "paradas" else 1
    hover = f"<b>%{{x|{formato_hover}}}</b><br>{titulo_eixo}: %{{y:,.{casas}f}}<extra>%{{fullData.name}}</extra>"

    for indice, grupo in enumerate(grupos):
        parte = serie[serie["grupo"] == grupo]
        cor = AZUL_ESCURO if len(grupos) == 1 else SEQUENCIA_CATEGORIAS[indice % len(SEQUENCIA_CATEGORIAS)]
        figura.add_scatter(
            x=parte["periodo"], y=parte[coluna], name=grupo, mode="lines+markers",
            line=dict(color=cor, width=2), marker=dict(size=5), hovertemplate=hover,
        )

    figura.update_layout(
        template="plotly_white",
        height=340,
        margin=dict(t=50, b=40, l=10, r=10),
        showlegend=len(grupos) > 1,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(tickformat=formato_eixo, title=None),
        yaxis=dict(title=titulo_eixo, rangemode="tozero"),
        font=dict(color=CINZA_ESCURO),
    )
    return figura


def grafico_turnos(resumo, coluna, titulo_eixo):
    """Barras por turno, uma cor por grupo (ou uma só, 'Todas')."""
    figura = go.Figure()
    grupos = list(dict.fromkeys(resumo["grupo"]))
    casas = {"paradas": 0, "tempo_horas": 1}.get(coluna, 2)
    hover = f"<b>Turno %{{x}}</b><br>{titulo_eixo}: %{{y:,.{casas}f}}<extra>%{{fullData.name}}</extra>"

    for indice, grupo in enumerate(grupos):
        parte = resumo[resumo["grupo"] == grupo]
        cor = AZUL_ESCURO if len(grupos) == 1 else SEQUENCIA_CATEGORIAS[indice % len(SEQUENCIA_CATEGORIAS)]
        figura.add_bar(
            x=parte["turno"], y=parte[coluna], name=grupo, marker_color=cor,
            text=[formatar_decimal(v, casas) for v in parte[coluna]],
            textposition="outside", cliponaxis=False, hovertemplate=hover,
        )

    topo = resumo[coluna].max()
    figura.update_layout(
        barmode="group",
        bargap=0.25,
        template="plotly_white",
        height=400,
        margin=dict(t=50, b=40, l=10, r=10),
        showlegend=len(grupos) > 1,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(type="category", title="Turno"),
        yaxis=dict(title=titulo_eixo, range=[0, topo * 1.18]),
        separators=",.",
        font=dict(color=CINZA_ESCURO),
    )
    return figura


def grafico_ranking(resumo, coluna, titulo_eixo):
    """Barras horizontais, da maior para a menor (o maior fica no topo)."""
    casas = 0 if coluna == "paradas" else 1
    topo = resumo[coluna].max()

    figura = go.Figure()
    figura.add_bar(
        x=resumo[coluna], y=resumo["grupo"], orientation="h", marker_color=AZUL_ESCURO,
        text=[formatar_decimal(v, casas) for v in resumo[coluna]],
        textposition="outside", cliponaxis=False,
        hovertemplate=f"<b>%{{y}}</b><br>{titulo_eixo}: %{{x:,.{casas}f}}<extra></extra>",
    )
    figura.update_layout(
        template="plotly_white",
        height=max(260, 44 * len(resumo) + 90),
        margin=dict(t=20, b=40, l=10, r=40),
        showlegend=False,
        yaxis=dict(autorange="reversed", automargin=True, title=None),
        xaxis=dict(title=titulo_eixo, range=[0, topo * 1.18]),
        separators=",.",
        font=dict(color=CINZA_ESCURO),
    )
    return figura


def grafico_pareto(resumo, titulo_eixo, casas=0):
    """Pareto: barras do valor de cada categoria e linha do percentual acumulado, com marca de 80%."""
    dados_hover = resumo[["pct", "pct_acumulado"]].to_numpy()
    mostrar_texto = len(resumo) <= 12

    figura = go.Figure()
    figura.add_bar(
        x=resumo["grupo"], y=resumo["valor"], name=titulo_eixo, marker_color=AZUL_ESCURO,
        text=[formatar_decimal(v, casas) for v in resumo["valor"]] if mostrar_texto else None,
        textposition="outside", cliponaxis=False, customdata=dados_hover,
        hovertemplate=(
            f"<b>%{{x}}</b><br>{titulo_eixo}: %{{y:,.{casas}f}}"
            "<br>Participação: %{customdata[0]:.1f}%<br>Acumulado: %{customdata[1]:.1f}%<extra></extra>"
        ),
    )
    figura.add_scatter(
        x=resumo["grupo"], y=resumo["pct_acumulado"], name="% acumulado", yaxis="y2",
        mode="lines+markers", line=dict(color=CINZA_ESCURO, width=2), marker=dict(size=6),
        hovertemplate="<b>%{x}</b><br>Acumulado: %{y:.1f}%<extra></extra>",
    )
    figura.add_shape(
        type="line", xref="paper", x0=0, x1=1, yref="y2", y0=80, y1=80,
        line=dict(color=CINZA, width=1, dash="dash"),
    )
    figura.add_annotation(
        xref="paper", x=1, yref="y2", y=80, text="80%", showarrow=False,
        xanchor="right", yshift=9, font=dict(color=CINZA_ESCURO, size=11),
    )

    figura.update_layout(
        template="plotly_white",
        height=480,
        margin=dict(t=50, b=40, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(type="category", tickangle=-35, automargin=True, title=None),
        yaxis=dict(title=titulo_eixo, range=[0, resumo["valor"].max() * 1.18]),
        yaxis2=dict(overlaying="y", side="right", range=[0, 105], ticksuffix="%", showgrid=False, title=None),
        separators=",.",
        font=dict(color=CINZA_ESCURO),
    )
    return figura


def grafico_mapa_calor(matriz, titulo, casas=0):
    """Mapa de calor: dias da semana (linhas) x hora do dia (colunas)."""
    figura = go.Figure(
        go.Heatmap(
            z=matriz.to_numpy(),
            x=[f"{hora:02d}h" for hora in matriz.columns],
            y=list(matriz.index),
            colorscale=[[0, "#F7FAFC"], [1, AZUL_ESCURO]],
            xgap=2, ygap=2,
            texttemplate=f"%{{z:,.{casas}f}}",
            textfont=dict(size=10),
            colorbar=dict(title=titulo, thickness=12),
            hovertemplate=f"<b>%{{y}}, %{{x}}</b><br>{titulo}: %{{z:,.{casas}f}}<extra></extra>",
        )
    )
    figura.update_layout(
        template="plotly_white",
        height=420,
        margin=dict(t=20, b=40, l=10, r=10),
        xaxis=dict(type="category", title="Hora de início da parada"),
        yaxis=dict(autorange="reversed", title=None),
        separators=",.",
        font=dict(color=CINZA_ESCURO),
    )
    return figura
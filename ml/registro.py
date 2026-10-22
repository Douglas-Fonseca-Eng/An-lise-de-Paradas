"""
Registro dos módulos preditivos planejados.

Por enquanto são apenas definições: nenhum modelo foi treinado e nenhuma previsão é gerada.
Quando um módulo for implementado, o status dele passa a "treinado".
"""
from ml.contrato import (NAO_TREINADO, TIPO_CLASSIFICACAO, TIPO_CONTAGEM, TIPO_INDICE,
                         DefinicaoModulo)

METRICAS_CLASSIFICACAO = ("Precision", "Recall", "F1-score", "ROC-AUC", "PR-AUC", "Matriz de confusão")
METRICAS_CONTAGEM = ("MAE", "RMSE", "Desvio de Poisson", "MedAE")

MODULOS = (
    DefinicaoModulo(
        id="microparadas_parada_relevante",
        nome="Microparadas → parada relevante",
        descricao=(
            "Analisa o histórico recente de microparadas e calcula a probabilidade de uma parada "
            "relevante nos próximos 30, 60 e 120 minutos."
        ),
        tipo=TIPO_CLASSIFICACAO,
        alvo="Ocorrência de parada relevante dentro do horizonte, por CT.",
        horizontes_min=(30, 60, 120),
        features_planejadas=(
            "microparadas_10min", "microparadas_20min", "microparadas_40min", "microparadas_60min",
            "duracao_media_recente", "duracao_maxima_recente", "intervalo_medio", "menor_intervalo",
            "tendencia_intervalos", "motivos_recentes", "origens_recentes", "ct", "turno", "hora",
            "tempo_desde_ultima_parada_relevante",
        ),
        algoritmos_candidatos=("Regressão Logística", "Random Forest", "XGBoost", "CatBoost"),
        baseline="Regra simples: mais de X microparadas na janela dispara um alerta.",
        metricas=METRICAS_CLASSIFICACAO,
        pendencias=(
            'Definir o que é uma "parada relevante" (por exemplo, duração mínima em minutos).',
            "Definir o valor de X da regra simples usada como baseline.",
        ),
        status=NAO_TREINADO,
    ),
    DefinicaoModulo(
        id="reincidencia_apos_retorno",
        nome="Reincidência após o retorno",
        descricao=(
            "Quando a máquina volta de uma parada, calcula a probabilidade de uma nova parada "
            "em 15, 30 e 60 minutos."
        ),
        tipo=TIPO_CLASSIFICACAO,
        alvo="Nova parada dentro do horizonte, contado a partir do retorno da máquina.",
        horizontes_min=(15, 30, 60),
        features_planejadas=(
            "duracao_da_parada_anterior", "motivo", "origem", "ct", "microparadas_anteriores",
            "numero_de_paradas_recentes", "intervalo_entre_ultimas_paradas",
            "reincidencias_anteriores", "horario", "turno",
        ),
        algoritmos_candidatos=("Regressão Logística", "Random Forest", "XGBoost", "CatBoost"),
        baseline="Regra simples baseada na taxa histórica de reincidência por CT.",
        metricas=METRICAS_CLASSIFICACAO,
        pendencias=(
            "Definir se a nova parada precisa ser relevante ou pode ser qualquer parada.",
        ),
        status=NAO_TREINADO,
    ),
    DefinicaoModulo(
        id="indice_instabilidade",
        nome="Índice de instabilidade",
        descricao=(
            "Gera um indicador de 0 a 100 do estado operacional de cada CT, com significado "
            "estatístico e explicável. Não pode ser um número arbitrário."
        ),
        tipo=TIPO_INDICE,
        alvo="Índice de instabilidade por CT, de 0 a 100.",
        features_planejadas=(
            "frequencia_de_paradas", "duracao", "reincidencia", "intervalo",
            "crescimento_das_microparadas", "anomalias", "probabilidade_de_evento_futuro",
        ),
        algoritmos_candidatos=("A definir a partir dos dados",),
        baseline="Percentil histórico simples da taxa de paradas da CT.",
        metricas=("A definir",),
        pendencias=(
            "Definir os componentes do índice e como combiná-los, com critério estatístico (sem pesos arbitrários).",
        ),
        status=NAO_TREINADO,
    ),
    DefinicaoModulo(
        id="previsao_proximo_turno",
        nome="Previsão do próximo turno",
        descricao=(
            "Prevê a quantidade de paradas (dado de contagem) e o tempo total de indisponibilidade "
            "do próximo turno, com faixa de incerteza."
        ),
        tipo=TIPO_CONTAGEM,
        alvo="Quantidade de paradas e minutos parados no próximo turno, por CT.",
        features_planejadas=(
            "paradas_nos_ultimos_turnos", "tempo_parado_nos_ultimos_turnos", "microparadas_recentes",
            "turno", "dia_da_semana", "ct",
        ),
        algoritmos_candidatos=("Regressão de Poisson", "Binomial Negativa", "Random Forest", "XGBoost", "CatBoost"),
        baseline="Média dos últimos turnos equivalentes (mesmo turno, mesma CT).",
        metricas=METRICAS_CONTAGEM,
        pendencias=(
            "Definir quantos turnos de histórico são necessários para gerar a primeira previsão.",
        ),
        status=NAO_TREINADO,
    ),
)


def listar_modulos():
    """Todos os módulos planejados, na ordem de apresentação."""
    return MODULOS


def obter_modulo(id_modulo):
    """Procura um módulo pelo id. Devolve None se não existir."""
    return next((modulo for modulo in MODULOS if modulo.id == id_modulo), None)
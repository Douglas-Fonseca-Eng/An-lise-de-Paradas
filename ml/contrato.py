"""
Contrato que todo módulo preditivo deve seguir.

Cada módulo (microparadas, reincidência, índice de instabilidade, previsão do próximo turno)
terá uma DEFINIÇÃO (quem é, o que prevê, com quais dados, como será avaliado) e uma
IMPLEMENTAÇÃO que cumpre as quatro etapas abaixo. O dashboard só conversa com este contrato,
então trocar ou acrescentar um modelo não exige reconstruir o software.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

NAO_TREINADO = "não treinado"
TREINADO = "treinado"

TIPO_CLASSIFICACAO = "classificação"
TIPO_CONTAGEM = "contagem"
TIPO_INDICE = "índice"


@dataclass(frozen=True)
class DefinicaoModulo:
    """Descrição de um módulo preditivo. É só informação: não contém nenhum modelo."""

    id: str
    nome: str
    descricao: str
    tipo: str
    alvo: str
    horizontes_min: tuple = ()
    features_planejadas: tuple = ()
    algoritmos_candidatos: tuple = ()
    baseline: str = ""
    metricas: tuple = ()
    pendencias: tuple = ()
    status: str = NAO_TREINADO


class ModuloPreditivo(ABC):
    """
    Molde de um módulo preditivo treinado. As quatro etapas são obrigatórias.
    Enquanto um módulo não tiver implementação, ele existe apenas como DefinicaoModulo.
    """

    definicao: DefinicaoModulo

    @abstractmethod
    def construir_dataset(self, paradas):
        """Monta a tabela de treino a partir das paradas, usando só informação anterior ao evento."""

    @abstractmethod
    def treinar(self, dataset):
        """Treina o modelo. A divisão dos dados deve ser temporal (antigo -> treino, recente -> teste)."""

    @abstractmethod
    def prever(self, dados_recentes):
        """Gera previsões, sempre com contexto (probabilidade, intervalo e fatores principais)."""

    @abstractmethod
    def avaliar(self, dataset):
        """Calcula as métricas adequadas e compara com o baseline de regra simples."""
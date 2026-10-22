# Módulos de Machine Learning

Esta pasta guarda a base para os modelos preditivos do projeto.

> **Nenhum modelo foi treinado ainda**, e o dashboard não mostra previsões.

## Estrutura

```
ml/
├── contrato.py     # molde dos módulos: DefinicaoModulo e ModuloPreditivo
├── registro.py     # os quatro módulos planejados, com suas fichas
├── features/       # construção das variáveis de entrada
├── models/         # código de cada módulo preditivo
├── evaluation/     # divisão temporal, métricas e baselines
└── predictions/    # gravação das previsões no banco
```

Os modelos treinados (arquivos) ficam em `data/modelos/`, fora do Git.

## Princípios

- **Divisão temporal:** dados antigos para treino, intermediários para validação e os mais recentes para teste. Sem divisão aleatória.
- **Sem vazamento de dados:** uma variável só pode usar informação que existia **antes** do evento previsto.
- **Baseline:** todo modelo é comparado com uma regra simples. Se não agregar valor, não entra.
- **Métricas adequadas:** classificação com Precision, Recall, F1, ROC-AUC, PR-AUC e matriz de confusão; contagem com MAE, RMSE e desvio de Poisson. Nunca apenas acurácia.
- **Explicabilidade:** toda previsão vem acompanhada dos fatores que a explicam (importância de variáveis e SHAP).
- **Nada de previsões falsas:** sem módulo treinado, o dashboard mostra "Módulo preditivo ainda não treinado".

## Como acrescentar um módulo

1. Ajustar a ficha (`DefinicaoModulo`) em `registro.py` e resolver as pendências de definição.
2. Construir as variáveis em `features/`.
3. Escrever uma classe em `models/` que cumpra `ModuloPreditivo` (dataset, treino, previsão e avaliação).
4. Avaliar contra o baseline, com divisão temporal.
5. Só depois disso, mudar o status para `treinado`.

## Volume de dados

Hoje o projeto tem cerca de um mês de paradas. É pouco para modelos preditivos: o conjunto de teste, na divisão temporal, terá poucos dias. Os primeiros resultados serão exploratórios e ficam mais confiáveis conforme novos meses forem importados.
# Análise de Paradas Industriais

Sistema de apoio à decisão para análise de paradas de equipamentos industriais.

A partir de planilhas de apontamento de paradas, o sistema valida e padroniza os dados (ETL), grava tudo em um banco de dados e apresenta um dashboard analítico interativo. A arquitetura foi desenhada para receber módulos de Machine Learning no futuro, sem reconstruir o software.

> O sistema é de **análise e monitoramento**. Ele não controla equipamentos e não toma decisões automaticamente.

## Destaques

- **Quantidade x tempo parado:** diferencia máquinas com muitas paradas curtas de máquinas com poucas paradas longas, evitando conclusões baseadas só na contagem de ocorrências.
- **Análise por turno corrigida pela duração:** compara turnos de tamanhos diferentes por paradas por hora de turno.
- **Microparadas e rajadas:** frequência, intervalos e sequências de microparadas, com janelas de 10 a 120 minutos.
- **Importação segura:** nunca sobrescreve dados, recusa o mesmo arquivo duas vezes e registra a origem de cada parada.
- **Qualidade dos dados:** página dedicada, pensada para a futura etapa de Machine Learning.

## Fluxo dos dados

```
Excel/CSV -> Importador -> Validação -> Normalização/ETL -> Banco de dados
                                                                 |
                                         Camada analítica -> Dashboard
                                                                 |
                                  (futuro) Features -> Modelos de ML -> Previsões
```

O dashboard não lê a planilha: ele lê do banco, e as colunas derivadas que dependem de configuração (como microparada ou faixa de duração) são calculadas na leitura.

## Páginas do dashboard

| Página | O que responde |
|---|---|
| Visão geral | Indicadores executivos: total, tempo parado, média, mediana, maior parada, microparadas e paradas longas |
| Quantidade x indisponibilidade | Quem concentra mais paradas também concentra mais tempo parado? |
| Análise temporal | Como paradas e tempo parado evoluem por dia ou semana |
| Turnos | Comparação entre turnos, inclusive por máquina e por hora de turno |
| Máquinas | Visão detalhada de cada CT: motivos, origens, turnos e evolução |
| Pareto | Quais causas (motivo, origem, tag) concentram a maior parte do problema |
| Mapa de calor | Em quais dias da semana e horas as paradas se concentram |
| Microparadas | Frequência, intervalos e rajadas de microparadas |
| Eventos | Tabela das paradas com busca, ordenação, detalhes e exportação |
| Qualidade dos dados | Verificações de consistência, valores ausentes e variações de escrita |

Todas as páginas respeitam os **filtros globais** da barra lateral (período, CT, turno, faixa de duração, motivo, origem, tag, operador, área responsável e quebra), exceto Qualidade dos dados, que analisa o banco inteiro.

## Tecnologias

Python 3.12, Streamlit, Plotly, Pandas, NumPy, SQLAlchemy e SQLite. O uso do SQLAlchemy permite migrar para PostgreSQL trocando a URL de conexão.

## Instalação

Requisitos: Anaconda (ou Python 3.12) no Windows.

```
conda create -n paradas python=3.12
conda activate paradas
pip install -r requirements.txt
```

## Como executar

```
conda activate paradas
streamlit run app.py
```

O dashboard abre em `http://localhost:8501`.

## Como importar dados

1. Copie a planilha (aba `Paradas`) para a pasta `data/raw`.
2. Execute o script de importação:

```
python testar_importacao.py
```

O script mostra um resumo: quantos registros eram novos, quantos já existiam, quantos estavam repetidos no arquivo e quantos eram inválidos. Importar o mesmo arquivo de novo é recusado com segurança.

> A importação pela interface (upload, pré-validação e confirmação) está prevista para a próxima fase. O script acima é provisório.

## Estrutura do projeto

```
.
├── app.py                 # entrada do dashboard: navegação e barra lateral
├── pages/                 # páginas do dashboard
├── src/
│   ├── transformer.py     # ETL: nomes de colunas, datas, textos, CT, ausentes, duplicados, turnos
│   ├── importer.py        # importação para o banco (transação única, só registros novos)
│   ├── database.py        # conexão com o banco
│   ├── tabelas.py         # definição das tabelas
│   ├── analytics.py       # camada analítica: KPIs, resumos, séries, Pareto, rajadas
│   ├── filters.py         # filtros globais, recortes e busca
│   ├── quality.py         # verificações de qualidade dos dados
│   ├── charts.py          # gráficos Plotly
│   ├── components.py      # blocos visuais reutilizados
│   ├── dashboard.py       # dados em cache e barra lateral
│   └── utils.py           # formatação no padrão brasileiro
├── config/
│   ├── schema.py          # colunas esperadas e nomes internos
│   ├── settings.py        # limites, CTs conhecidas e caminho do banco
│   ├── shifts.py          # horários dos turnos
│   └── theme.py           # cores dos gráficos
├── data/                  # planilhas (conteúdo não versionado)
├── database/              # banco SQLite (conteúdo não versionado)
├── .streamlit/config.toml # tema do dashboard
├── testar_*.py            # scripts de verificação de cada etapa
└── requirements.txt
```

## Configuração

| O que ajustar | Onde |
|---|---|
| Horários e nomes dos turnos | `config/shifts.py` |
| Limite de microparada e limites de paradas longas | `config/settings.py` (`LIMITE_MICROPARADA_MIN`, `LIMITES_PARADA_LONGA_MIN`) |
| CTs conhecidas e apelidos de CT | `config/settings.py` (`CTS_CONHECIDOS`, `CT_ALIASES`) |
| Colunas esperadas, obrigatórias e nomes internos | `config/schema.py` |
| Cores dos gráficos | `config/theme.py` |

## Regras de tratamento dos dados

- **Colunas:** reconhecidas pelo nome normalizado (sem acentos, maiúsculas ou símbolos). São obrigatórias: ID, CT, Data Início, Data Fim e Duração. Colunas desconhecidas são mantidas e sinalizadas.
- **Valores ausentes:** o texto `-` é tratado como ausente em ACM, Nota Corretiva, Providência, Frequência e Motivo.
- **Início ausente:** é reconstruído como fim menos duração, e a parada recebe uma marca de aviso.
- **Fim ausente:** a parada é considerada em andamento, o fim não é inventado e a duração é provisória.
- **CT:** padronizada em maiúsculas e sem espaços. Apelidos só são aplicados depois de confirmados em `CT_ALIASES`, e uma CT fora da lista é sinalizada, nunca descartada.
- **Duplicidade:**
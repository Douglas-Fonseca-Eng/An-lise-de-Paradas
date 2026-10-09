# Análise de Paradas Industriais

Sistema de apoio à decisão para análise de paradas de equipamentos industriais.
Lê planilhas de apontamento de paradas, trata os dados (ETL), grava em um banco SQLite
e mostra um dashboard analítico em Streamlit. A arquitetura está preparada para receber
módulos de Machine Learning no futuro.

O sistema apenas analisa. Ele não controla equipamentos.

## Como executar

```
conda activate paradas
streamlit run app.py
```

## Dados

Os dados reais (planilhas e banco de dados) **não ficam neste repositório**. As pastas
`data/raw`, `data/processed` e `database` existem, mas o conteúdo delas é ignorado pelo Git.
"""
Schema interno do sistema de análise de paradas.

Cada item descreve uma coluna: como ela se chama na planilha (original),
como vamos chamá-la dentro do sistema (interno), o tipo esperado, se é
obrigatória e para que serve.
"""

COLUNAS = [
    {"original": "ID", "interno": "id_origem", "tipo": "inteiro", "obrigatoria": True,
     "descricao": "Identificador da parada no sistema de origem"},
    {"original": "Planta", "interno": "planta", "tipo": "texto", "obrigatoria": False,
     "descricao": "Planta onde a parada ocorreu"},
    {"original": "CT", "interno": "ct", "tipo": "texto", "obrigatoria": True,
     "descricao": "Centro de trabalho / máquina"},
    {"original": "Data Inicio", "interno": "data_inicio", "tipo": "data_hora", "obrigatoria": True,
     "descricao": "Início da parada"},
    {"original": "Data Fim", "interno": "data_fim", "tipo": "data_hora", "obrigatoria": True,
     "descricao": "Fim da parada"},
    {"original": "Quebra", "interno": "quebra", "tipo": "inteiro", "obrigatoria": False,
     "descricao": "Indicador de quebra (0 ou 1)"},
    {"original": "Frequência", "interno": "frequencia", "tipo": "inteiro", "obrigatoria": False,
     "descricao": "Indicador de frequência (0 ou 1)"},
    {"original": "Duração", "interno": "duracao", "tipo": "duracao", "obrigatoria": True,
     "descricao": "Duração da parada (hh:mm:ss)"},
    {"original": "Duração Decimal", "interno": "duracao_decimal_horas", "tipo": "decimal", "obrigatoria": False,
     "descricao": "Duração em horas decimais"},
    {"original": "Origem", "interno": "origem", "tipo": "texto", "obrigatoria": False,
     "descricao": "Classificação de origem da parada"},
    {"original": "Tag", "interno": "tag", "tipo": "texto", "obrigatoria": False,
     "descricao": "Tag do equipamento"},
    {"original": "Descrição da Tag", "interno": "descricao_tag", "tipo": "texto", "obrigatoria": False,
     "descricao": "Descrição da tag"},
    {"original": "Equipamento", "interno": "equipamento", "tipo": "texto", "obrigatoria": False,
     "descricao": "Equipamento envolvido (hoje vazia)"},
    {"original": "Modo Falha", "interno": "modo_falha", "tipo": "texto", "obrigatoria": False,
     "descricao": "Modo de falha (hoje vazia)"},
    {"original": "Causa Raiz", "interno": "causa_raiz", "tipo": "texto", "obrigatoria": False,
     "descricao": "Causa raiz (hoje vazia)"},
    {"original": "Motivo", "interno": "motivo", "tipo": "texto", "obrigatoria": False,
     "descricao": "Motivo da parada"},
    {"original": "Providência", "interno": "providencia", "tipo": "texto", "obrigatoria": False,
     "descricao": "Providência tomada"},
    {"original": "ACM", "interno": "acm", "tipo": "texto", "obrigatoria": False,
     "descricao": "ACM (hoje sem informação)"},
    {"original": "Nota Corretiva", "interno": "nota_corretiva", "tipo": "texto", "obrigatoria": False,
     "descricao": "Nota corretiva (hoje sem informação)"},
    {"original": "Operador", "interno": "operador", "tipo": "texto", "obrigatoria": False,
     "descricao": "Operador que apontou a parada"},
    {"original": "Área Responsável", "interno": "area_responsavel", "tipo": "texto", "obrigatoria": False,
     "descricao": "Área responsável pela parada"},
    {"original": "Último Usuário", "interno": "ultimo_usuario", "tipo": "texto", "obrigatoria": False,
     "descricao": "Último usuário que alterou o registro"},
]

# Regra A (aprovada): nestas colunas, o texto "-" significa "sem informação".
MARCADORES_VAZIO = ["-"]
COLUNAS_COM_MARCADOR_VAZIO = ["frequencia", "motivo", "providencia", "acm", "nota_corretiva"]

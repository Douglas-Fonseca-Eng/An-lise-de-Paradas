"""Configurações gerais do sistema."""
from pathlib import Path

# CTs (máquinas) conhecidos. Um CT fora desta lista é sinalizado, nunca descartado.
CTS_CONHECIDOS = ["SBL-P2", "SBL-P3", "SBL-P4", "SBL-P5"]

# Apelidos de CT -> nome padrão. Fica VAZIO de propósito:
# só adicione um apelido (por exemplo "P4": "SBL-P4") depois de confirmar
# que é mesmo a mesma máquina. As chaves devem estar em MAIÚSCULAS.
CT_ALIASES = {}

# Microparada: parada com duração de até este valor, em minutos (inclusive).
LIMITE_MICROPARADA_MIN = 1

# Limites das paradas "longas", em minutos. Parada acima de 5 min, acima de 30 min, acima de 1 h.
LIMITES_PARADA_LONGA_MIN = [5, 30, 60]


# Banco de dados. A pasta do projeto é descoberta a partir deste arquivo,
# então o caminho funciona mesmo que o programa seja executado de outra pasta.
RAIZ_PROJETO = Path(__file__).resolve().parent.parent
CAMINHO_BANCO = RAIZ_PROJETO / "database" / "paradas.db"
URL_BANCO = f"sqlite:///{CAMINHO_BANCO.as_posix()}"
# Cópia de cada arquivo importado pela interface (fica fora do Git, junto com os demais dados).
PASTA_IMPORTADOS = RAIZ_PROJETO / "data" / "importados"
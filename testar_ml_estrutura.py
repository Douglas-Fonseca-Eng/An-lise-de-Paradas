from ml.contrato import NAO_TREINADO, DefinicaoModulo, ModuloPreditivo
from ml.registro import listar_modulos, obter_modulo

modulos = listar_modulos()
print("Módulos preditivos registrados:", len(modulos))
for modulo in modulos:
    print(f"- {modulo.id} | {modulo.nome} | {modulo.tipo} | status: {modulo.status}")

print("\nTodos não treinados:", all(modulo.status == NAO_TREINADO for modulo in modulos))
print("Ids únicos:", len({modulo.id for modulo in modulos}) == len(modulos))
print("Módulo inexistente:", obter_modulo("nao_existe"))

print("\nHorizontes (min):")
for modulo in modulos:
    print(f"  {modulo.id}: {modulo.horizontes_min or 'não se aplica'}")

print("\nPendências de definição:")
for modulo in modulos:
    for pendencia in modulo.pendencias:
        print(f"  [{modulo.id}] {pendencia}")

print("\nContrato:")
try:
    ModuloPreditivo()
except TypeError as erro:
    print("  ModuloPreditivo não pode ser usado diretamente:", str(erro)[:70], "...")

try:
    modulos[0].status = "treinado"
except Exception as erro:
    print("  Definições são imutáveis:", type(erro).__name__)
print("  Campos da definição:", len(DefinicaoModulo.__dataclass_fields__))
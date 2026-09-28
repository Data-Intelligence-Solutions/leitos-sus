"""
Promove a staging para a silver, com segurança.

Como usar (na pasta do projeto, com o .venv ativo):
    python -m src.promover_silver

O que faz, em ordem:
    1. Roda os testes de qualidade da staging (SIH, CNES e população).
    2. Só se todos passarem, copia os 3 arquivos de data/staging para data/silver.
    3. Roda o teste que confere se staging e silver ficaram iguais.

Se algum teste falhar, nada é copiado e a silver continua como estava.
"""

import shutil
import subprocess
import sys

from src.config import (
    CNES_SILVER_PATH,
    CNES_STAGING_PATH,
    POPULACAO_SILVER_PATH,
    POPULACAO_STAGING_PATH,
    PROJECT_ROOT,
    SIH_SILVER_PATH,
    SIH_STAGING_PATH,
    SILVER_DIR,
)

ARQUIVOS = [
    (SIH_STAGING_PATH, SIH_SILVER_PATH),
    (CNES_STAGING_PATH, CNES_SILVER_PATH),
    (POPULACAO_STAGING_PATH, POPULACAO_SILVER_PATH),
]

TESTES_QUALIDADE = ["tests/test_sih.py", "tests/test_cnes.py", "tests/test_populacao.py"]
TESTE_IGUALDADE = ["tests/test_staging_silver.py"]


# Roda o pytest com o mesmo Python que está rodando este script

def rodar_testes(arquivos: list[str]) -> bool:
    resultado = subprocess.run([sys.executable, "-m", "pytest", "-q", *arquivos], cwd=PROJECT_ROOT)
    return resultado.returncode == 0


def promover_silver() -> None:
    faltando = [origem.name for origem, _ in ARQUIVOS if not origem.exists()]
    if faltando:
        raise SystemExit(f"ERRO: staging incompleta ({faltando}). Rode antes: python -m src.pipeline")

    print("1/3 Testando a qualidade da staging...")
    if not rodar_testes(TESTES_QUALIDADE):
        raise SystemExit("\nERRO: a staging não passou nos testes. Nada foi copiado para a silver.")

    print("\n2/3 Copiando staging -> silver...")
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    for origem, destino in ARQUIVOS:
        try:
            shutil.copy2(origem, destino)
        except PermissionError:
            raise SystemExit(f"\nERRO: {destino.name} está aberto em outro programa. Feche e rode de novo.")
        print(f"  OK  {origem.name}")

    print("\n3/3 Conferindo se staging e silver ficaram iguais...")
    if not rodar_testes(TESTE_IGUALDADE):
        raise SystemExit("\nERRO: staging e silver ficaram diferentes. Verifique a mensagem acima.")

    print("\nPronto. Silver atualizada. Próximo passo: python gerar_modelo_bi_girosus.py")


if __name__ == "__main__":
    promover_silver()

from prefect import flow, task

from src.config import STAGING_DIR
from src.pipeline import (
    processar_cnes,
    processar_populacao,
    processar_sih,
)

# Tarefas do Prefect

@task(name="Processar SIH")
def tarefa_sih() -> None:
    processar_sih()


@task(name="Processar CNES")
def tarefa_cnes() -> None:
    processar_cnes()


@task(name="Processar população")
def tarefa_populacao() -> None:
    processar_populacao()


# Orquestra o pipeline

@flow(name="pipeline-leitos-sus")
def executar_fluxo() -> None:
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    tarefa_sih()
    tarefa_cnes()
    tarefa_populacao()


if __name__ == "__main__":
    executar_fluxo()

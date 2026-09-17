from src.config import (
    CNES_STAGING_PATH,
    POPULACAO_STAGING_PATH,
    SIH_STAGING_PATH,
    STAGING_DIR,
)
from src.extract.cnes import extrair_cnes
from src.extract.ibge import extrair_ibge
from src.extract.sih import extrair_sih
from src.transform.cnes import transformar_cnes
from src.transform.populacao import transformar_populacao
from src.transform.sih import transformar_sih

# Processa o SIH

def processar_sih() -> None:
    df = transformar_sih(extrair_sih())

    df.to_parquet(SIH_STAGING_PATH, index=False)


# Processa o CNES

def processar_cnes() -> None:
    df = transformar_cnes(extrair_cnes())

    df.to_parquet(CNES_STAGING_PATH, index=False)


# Processa a população

def processar_populacao() -> None:
    df = transformar_populacao(extrair_ibge())

    df.to_parquet(POPULACAO_STAGING_PATH, index=False)


# Executa o pipeline

def executar_pipeline() -> None:
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    processar_sih()
    processar_cnes()
    processar_populacao()


if __name__ == "__main__":
    executar_pipeline()

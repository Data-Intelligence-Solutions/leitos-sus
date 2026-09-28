from time import perf_counter

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


# Mostra na tela o que foi gravado

def informar(nome: str, df, caminho, inicio: float) -> None:
    linhas = f"{len(df):,}".replace(",", ".")
    print(f"  OK  {nome}: {linhas} linhas, {df.shape[1]} colunas -> {caminho.name} "
          f"({perf_counter() - inicio:.0f}s)")


# Processa o SIH

def processar_sih() -> None:
    inicio = perf_counter()
    print("SIH: lendo os arquivos mensais...")
    df = transformar_sih(extrair_sih())

    df.to_parquet(SIH_STAGING_PATH, index=False)
    informar("SIH", df, SIH_STAGING_PATH, inicio)


# Processa o CNES

def processar_cnes() -> None:
    inicio = perf_counter()
    print("CNES: lendo os arquivos mensais...")
    df = transformar_cnes(extrair_cnes())

    df.to_parquet(CNES_STAGING_PATH, index=False)
    informar("CNES", df, CNES_STAGING_PATH, inicio)


# Processa a população

def processar_populacao() -> None:
    inicio = perf_counter()
    print("População: lendo as planilhas do IBGE...")
    df = transformar_populacao(extrair_ibge())

    df.to_parquet(POPULACAO_STAGING_PATH, index=False)
    informar("População", df, POPULACAO_STAGING_PATH, inicio)


# Executa o pipeline

def executar_pipeline() -> None:
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Pipeline leitos-sus: gravando em {STAGING_DIR}")

    processar_sih()
    processar_cnes()
    processar_populacao()

    print("\nPronto. Próximo passo: python -m src.promover_silver")


if __name__ == "__main__":
    executar_pipeline()

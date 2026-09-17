import pyarrow.parquet as pq

from src.config import (
    CNES_SILVER_PATH,
    CNES_STAGING_PATH,
    POPULACAO_SILVER_PATH,
    POPULACAO_STAGING_PATH,
    SIH_SILVER_PATH,
    SIH_STAGING_PATH,
)

# Compara duas bases Parquet

def comparar_parquets(staging_path, silver_path):
    staging = pq.ParquetFile(staging_path)
    silver = pq.ParquetFile(silver_path)

    assert staging.metadata.num_rows == silver.metadata.num_rows

    assert staging.schema_arrow.equals(silver.schema_arrow, check_metadata=False)

    for coluna in staging.schema_arrow.names:
        staging_coluna = pq.read_table(staging_path, columns=[coluna])

        silver_coluna = pq.read_table(silver_path, columns=[coluna])

        assert staging_coluna.equals(
            silver_coluna, check_metadata=False
        ), f"Diferença encontrada na coluna: {coluna}"


# SIH

def test_sih_staging_igual_silver():
    comparar_parquets(SIH_STAGING_PATH, SIH_SILVER_PATH)


# CNES

def test_cnes_staging_igual_silver():
    comparar_parquets(CNES_STAGING_PATH, CNES_SILVER_PATH)


# População

def test_populacao_staging_igual_silver():
    comparar_parquets(POPULACAO_STAGING_PATH, POPULACAO_SILVER_PATH)

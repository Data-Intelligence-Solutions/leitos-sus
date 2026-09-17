import pandas as pd
import pytest

from src.config import (
    CNES_STAGING_PATH,
    POPULACAO_STAGING_PATH,
    SIH_STAGING_PATH,
)
# Base do SIH

@pytest.fixture(scope="session")
def df_sih() -> pd.DataFrame:
    return pd.read_parquet(SIH_STAGING_PATH)

# Base do CNES

@pytest.fixture(scope="session")
def df_cnes() -> pd.DataFrame:
    return pd.read_parquet(CNES_STAGING_PATH)


# Base de população

@pytest.fixture(scope="session")
def df_populacao() -> pd.DataFrame:
    return pd.read_parquet(POPULACAO_STAGING_PATH)

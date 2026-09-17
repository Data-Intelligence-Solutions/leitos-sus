from pathlib import Path

# Projeto
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Diretórios de dados

DATA_DIR = PROJECT_ROOT / "data"

RAW_DIR = DATA_DIR / "raw"
STAGING_DIR = DATA_DIR / "staging"
SILVER_DIR = DATA_DIR / "silver"

# Fontes

SIH_RAW_DIR = RAW_DIR / "sih"
CNES_RAW_DIR = RAW_DIR / "cnes"
IBGE_RAW_DIR = RAW_DIR / "ibge"

# Periodo de projeto
ANO_INICIAL = 2021
ANO_FINAL = 2026
ANOS = range(ANO_INICIAL, ANO_FINAL + 1)

# Localidade
UF = "GO"
CODIGO_UF = "52"

# Saída temporal do ETL

SIH_STAGING_PATH = STAGING_DIR / "sih_multianual.parquet"

CNES_STAGING_PATH = STAGING_DIR / "cnes_multianual.parquet"

POPULACAO_STAGING_PATH = STAGING_DIR / "populacao_multianual.parquet"

# Base silver já validadas
SIH_SILVER_PATH = SILVER_DIR / "sih_multianual.parquet"

CNES_SILVER_PATH = SILVER_DIR / "cnes_multianual.parquet"

POPULACAO_SILVER_PATH = SILVER_DIR / "populacao_multianual.parquet"

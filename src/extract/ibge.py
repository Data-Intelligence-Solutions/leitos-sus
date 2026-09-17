import pandas as pd

from src.config import IBGE_RAW_DIR

# Arquivos de população
ARQUIVOS_IBGE = {
    2021: {
        "arquivo": IBGE_RAW_DIR / "estimativas" / "2021" / "estimativa_dou_2021.xls",
        "aba": "Municípios",
    },
    2022: {
        "arquivo": IBGE_RAW_DIR
        / "tcu_2023"
        / "POP_TCU_2023_Municipios_POP2022_Malha2023.xls",
        "aba": "Municípios",
    },
    2024: {
        "arquivo": IBGE_RAW_DIR / "estimativas" / "2024" / "estimativa_dou_2024.xls",
        "aba": "MUNICÍPIOS",
    },
    2025: {
        "arquivo": IBGE_RAW_DIR / "estimativas" / "2025" / "estimativa_dou_2025.xls",
        "aba": "Municípios",
    },
    2026: {
        "arquivo": IBGE_RAW_DIR / "estimativas" / "2026" / "estimativa_dou_2026.xlsx",
        "aba": "municípios",
    },
}


# Carrega uma fonte populacional
def extrair_populacao_ano(ano: int) -> pd.DataFrame:
    if ano not in ARQUIVOS_IBGE:
        raise ValueError(f"Não existe fonte bruta de população configurada para {ano}.")

    fonte = ARQUIVOS_IBGE[ano]

    if not fonte["arquivo"].exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {fonte['arquivo']}")

    return pd.read_excel(
        fonte["arquivo"],
        sheet_name=fonte["aba"],
        header=1,
        dtype={
            "COD. UF": str,
            "COD. MUNIC": str,
        },
    )


# Carrega todas as fontes populacionais
def extrair_ibge() -> dict[int, pd.DataFrame]:
    return {ano: extrair_populacao_ano(ano) for ano in ARQUIVOS_IBGE}

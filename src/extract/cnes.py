from pathlib import Path

import pandas as pd

from src.config import ANOS, CNES_RAW_DIR

# Colunas utilizadas no projeto
COLUNAS_CNES = [
    "CNES",
    "CODUFMUN",
    "TP_UNID",
    "TP_LEITO",
    "CODLEITO",
    "QT_EXIST",
    "QT_SUS",
    "QT_NSUS",
    "COMPETEN",
]


# Localiza os arquivos mensais do CNES
def listar_arquivos_cnes() -> list[Path]:
    arquivos = []

    for ano in ANOS:
        pasta_ano = CNES_RAW_DIR / str(ano)

        arquivos.extend(pasta_ano.glob("LTGO*.parquet"))

    return sorted(arquivos)


# Carrega e consolida os arquivos do CNES
def extrair_cnes() -> pd.DataFrame:
    arquivos = listar_arquivos_cnes()

    if not arquivos:
        raise FileNotFoundError("Nenhum arquivo do CNES foi encontrado.")

    partes = []

    for arquivo in arquivos:
        df = pd.read_parquet(arquivo, columns=COLUNAS_CNES)

        df["ARQUIVO_ORIGEM"] = arquivo.with_suffix(".dbc").name

        partes.append(df)

    return pd.concat(partes, ignore_index=True)

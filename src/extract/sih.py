from pathlib import Path
import pandas as pd
from src.config import ANOS, SIH_RAW_DIR

# Colunas utilizadas no projeto
COLUNAS_SIH = [
    "ANO_CMPT",
    "MES_CMPT",
    "N_AIH",
    "IDENT",
    "SEQ_AIH5",
    "CNES",
    "MUNIC_RES",
    "MUNIC_MOV",
    "DT_INTER",
    "DT_SAIDA",
    "DIAS_PERM",
    "UTI_MES_TO",
    "VAL_TOT",
    "DIAG_PRINC",
    "MORTE",
    "ESPEC",
    "PROC_REA",
    "CAR_INT",
    "SEXO",
    "IDADE",
    "COD_IDADE",
    "GESTAO",
]

# Localiza os arquivos mensais do SIH

def listar_arquivos_sih() -> list[Path]:
    arquivos = []

    for ano in ANOS:
        pasta_ano = SIH_RAW_DIR / str(ano)
        arquivos.extend(pasta_ano.glob("RDGO*.parquet"))

    return sorted(arquivos)


# Carrega e consolida os arquivos do SIH

def extrair_sih() -> pd.DataFrame:
    arquivos = listar_arquivos_sih()

    if not arquivos:
        raise FileNotFoundError("Nenhum arquivo do SIH foi encontrado.")

    partes = []

    for arquivo in arquivos:
        df = pd.read_parquet(arquivo, columns=COLUNAS_SIH)
        df["ARQUIVO_ORIGEM"] = arquivo.with_suffix(".dbc").name
        partes.append(df)

    return pd.concat(partes, ignore_index=True)

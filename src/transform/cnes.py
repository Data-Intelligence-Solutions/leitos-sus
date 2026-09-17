import pandas as pd

# Colunas de quantidade de leitos
COLUNAS_QUANTIDADE = [
    "QT_EXIST",
    "QT_SUS",
    "QT_NSUS",
]

# Transforma os dados do CNES
def transformar_cnes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["ANO"] = df["ARQUIVO_ORIGEM"].str[4:6].astype(int) + 2000

    df["MES"] = df["ARQUIVO_ORIGEM"].str[6:8].astype(int)

    for coluna in COLUNAS_QUANTIDADE:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    return df

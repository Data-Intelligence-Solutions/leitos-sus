import pandas as pd

# Transforma os dados do SIH
def transformar_sih(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["DT_INTER"] = pd.to_datetime(df["DT_INTER"], errors="raise").dt.date
    return df

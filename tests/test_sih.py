# Cobertura temporal do SIH

def test_cobertura_temporal_sih(df_sih):
    competencias = (
        df_sih[["ANO_CMPT", "MES_CMPT"]]
        .drop_duplicates()
        .sort_values(["ANO_CMPT", "MES_CMPT"])
    )

    assert len(competencias) == 66
    assert tuple(competencias.iloc[0]) == ("2021", "01")
    assert tuple(competencias.iloc[-1]) == ("2026", "06")


# Códigos municipais válidos

def test_codigos_municipais_sih_validos(df_sih):
    assert df_sih["MUNIC_RES"].str.fullmatch(r"\d{6}", na=False).all()
    assert df_sih["MUNIC_MOV"].str.fullmatch(r"\d{6}", na=False).all()


import pandas as pd

# Colunas críticas sem valores nulos

def test_colunas_criticas_sih_sem_nulos(df_sih):
    colunas_criticas = [
        "ANO_CMPT",
        "MES_CMPT",
        "N_AIH",
        "CNES",
        "MUNIC_RES",
        "MUNIC_MOV",
        "DT_INTER",
        "DT_SAIDA",
        "ARQUIVO_ORIGEM",
    ]

    nulos = df_sih[colunas_criticas].isna().sum().sum()

    assert nulos == 0

# Datas válidas do SIH

def test_datas_sih_validas(df_sih):
    datas_saida = pd.to_datetime(df_sih["DT_SAIDA"], format="%Y%m%d", errors="coerce")

    assert df_sih["DT_INTER"].notna().all()
    assert datas_saida.notna().all()

# Chave única do CNES

def test_chave_cnes_sem_duplicados(df_cnes):
    duplicados = df_cnes.duplicated(
        subset=[
            "CNES",
            "TP_LEITO",
            "CODLEITO",
            "COMPETEN",
        ]
    ).sum()

    assert duplicados == 0


# Consistência da quantidade de leitos

def test_quantidade_leitos_consistente(df_cnes):
    inconsistencias = (
        df_cnes["QT_EXIST"] != (df_cnes["QT_SUS"] + df_cnes["QT_NSUS"])
    ).sum()

    assert inconsistencias == 0


# Cobertura temporal do CNES

def test_cobertura_temporal_cnes(df_cnes):
    competencias = df_cnes[["ANO", "MES"]].drop_duplicates().sort_values(["ANO", "MES"])

    assert len(competencias) == 67
    assert tuple(competencias.iloc[0]) == (2021, 1)
    assert tuple(competencias.iloc[-1]) == (2026, 7)


# Colunas críticas sem valores nulos

def test_colunas_criticas_cnes_sem_nulos(df_cnes):
    colunas_criticas = [
        "CNES",
        "CODUFMUN",
        "TP_LEITO",
        "CODLEITO",
        "QT_EXIST",
        "QT_SUS",
        "QT_NSUS",
        "COMPETEN",
        "ANO",
        "MES",
    ]

    nulos = df_cnes[colunas_criticas].isna().sum().sum()

    assert nulos == 0

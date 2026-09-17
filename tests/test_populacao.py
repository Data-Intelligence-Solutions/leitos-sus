# Chave única da população

def test_chave_populacao_sem_duplicados(df_populacao):
    duplicados = df_populacao.duplicated(
        subset=[
            "codigo_ibge_7",
            "ano_referencia",
        ]
    ).sum()

    assert duplicados == 0


# Códigos municipais válidos

def test_codigos_ibge_validos(df_populacao):
    codigos_validos = df_populacao["codigo_ibge_7"].str.fullmatch(r"\d{7}", na=False)

    assert codigos_validos.all()


# Cobertura temporal da população

def test_cobertura_temporal_populacao(df_populacao):
    anos = sorted(df_populacao["ano_referencia"].unique().tolist())

    assert anos == [
        2021,
        2022,
        2023,
        2024,
        2025,
        2026,
    ]


# Proveniência da população de 2023

def test_proveniencia_populacao_2023(df_populacao):
    df_2023 = df_populacao[df_populacao["ano_referencia"] == 2023]

    assert len(df_2023) == 5570
    assert df_2023["ano_publicacao"].isna().all()
    assert (df_2023["origem"] == "Cálculo próprio com dados IBGE").all()
    assert (df_2023["tipo_dado"] == "População interpolada entre 2022 e 2024").all()

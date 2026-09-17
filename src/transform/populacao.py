import pandas as pd

# Colunas finais
COLUNAS_POPULACAO = [
    "uf",
    "cod_uf",
    "cod_municipio",
    "municipio",
    "populacao",
    "codigo_ibge_7",
    "ano_referencia",
    "ano_publicacao",
    "origem",
    "tipo_dado",
]

# Coluna de população do Censo 2022
COLUNA_POPULACAO_2022 = (
    "POPULAÇÃO APURADA IBGE \n" "- CENSO DEMOGRÁFICO 2022 E MALHA TERRITORIAL 2023 -"
)

# Padroniza as estimativas populacionais


def _padronizar_estimativa(df: pd.DataFrame, ano: int) -> pd.DataFrame:
    df = df.copy()

    df = df.rename(
        columns={
            "UF": "uf",
            "COD. UF": "cod_uf",
            "COD. MUNIC": "cod_municipio",
            "NOME DO MUNICÍPIO": "municipio",
            "POPULAÇÃO ESTIMADA": "populacao",
        }
    )

    df["cod_uf"] = df["cod_uf"].astype("string").str.strip().str.zfill(2)

    df["cod_municipio"] = df["cod_municipio"].astype("string").str.strip().str.zfill(5)

    df["codigo_ibge_7"] = df["cod_uf"] + df["cod_municipio"]

    populacao = (
        df["populacao"]
        .astype("string")
        .str.strip()
        .str.replace(r"\(\d+\)\s*$", "", regex=True)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(".", "", regex=False)
    )

    df["populacao"] = pd.to_numeric(populacao, errors="coerce").astype("Int64")

    df = df[df["codigo_ibge_7"].str.fullmatch(r"\d{7}", na=False)].copy()

    df["ano_referencia"] = ano
    df["ano_publicacao"] = ano
    df["origem"] = "IBGE"
    df["tipo_dado"] = "Estimativa populacional"

    return df[COLUNAS_POPULACAO]


# Padroniza a população do Censo 2022


def _padronizar_2022(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df = df.rename(
        columns={
            "UF": "uf",
            "COD. UF": "cod_uf",
            "COD. MUNIC": "cod_municipio",
            "NOME DO MUNICÍPIO": "municipio",
            COLUNA_POPULACAO_2022: "populacao",
        }
    )

    df["cod_uf"] = df["cod_uf"].astype("string").str.strip().str.zfill(2)

    df["cod_municipio"] = df["cod_municipio"].astype("string").str.strip().str.zfill(5)

    df["codigo_ibge_7"] = df["cod_uf"] + df["cod_municipio"]

    df = df[df["codigo_ibge_7"].str.fullmatch(r"\d{7}", na=False)].copy()

    populacao = (
        df["populacao"]
        .astype("string")
        .str.strip()
        .str.replace(r"\(\d+\)\s*$", "", regex=True)
        .str.strip()
        .str.replace(".", "", regex=False)
    )

    df["populacao"] = pd.to_numeric(populacao, errors="coerce").astype("Int64")

    df["ano_referencia"] = 2022
    df["ano_publicacao"] = 2023
    df["origem"] = "IBGE"
    df["tipo_dado"] = (
        "População municipal publicada pelo IBGE para o TCU "
        "- base Censo 2022 / Malha 2023"
    )

    return df[COLUNAS_POPULACAO]


# Consolida as fontes oficiais


def transformar_fontes_oficiais(dados: dict[int, pd.DataFrame]) -> pd.DataFrame:
    partes = [
        _padronizar_estimativa(dados[2021], 2021),
        _padronizar_2022(dados[2022]),
        _padronizar_estimativa(dados[2024], 2024),
        _padronizar_estimativa(dados[2025], 2025),
        _padronizar_estimativa(dados[2026], 2026),
    ]

    return pd.concat(partes, ignore_index=True)


# Calcula a população de referência de 2023

def _criar_populacao_2023(df: pd.DataFrame) -> pd.DataFrame:
    pop_2022 = df[df["ano_referencia"] == 2022].copy()

    pop_2024 = df[df["ano_referencia"] == 2024].copy()

    df_2023 = pop_2022[
        [
            "uf",
            "cod_uf",
            "cod_municipio",
            "municipio",
            "codigo_ibge_7",
            "populacao",
        ]
    ].merge(
        pop_2024[
            [
                "codigo_ibge_7",
                "populacao",
            ]
        ],
        on="codigo_ibge_7",
        how="inner",
        suffixes=("_2022", "_2024"),
        validate="one_to_one",
    )

    df_2023["populacao"] = (
        ((df_2023["populacao_2022"] + df_2023["populacao_2024"]) / 2)
        .round()
        .astype("Int64")
    )

    df_2023["ano_referencia"] = 2023
    df_2023["ano_publicacao"] = pd.NA
    df_2023["origem"] = "Cálculo próprio com dados IBGE"
    df_2023["tipo_dado"] = "População interpolada entre 2022 e 2024"

    return df_2023[COLUNAS_POPULACAO]

# Transforma as fontes populacionais

def transformar_populacao(dados: dict[int, pd.DataFrame]) -> pd.DataFrame:
    df = transformar_fontes_oficiais(dados)

    df_2023 = _criar_populacao_2023(df)

    df = pd.concat(
        [
            df,
            df_2023,
        ],
        ignore_index=True,
    )

    return df.sort_values(
        [
            "ano_referencia",
            "codigo_ibge_7",
        ]
    ).reset_index(drop=True)

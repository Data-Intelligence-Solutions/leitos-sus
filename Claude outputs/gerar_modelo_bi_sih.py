# -*- coding: utf-8 -*-
"""
Gera o modelo de fato e dimensao (somente SIH) pronto para o Power BI.

Como usar:
    1. Ative o ambiente virtual do projeto (.venv).
    2. Rode este arquivo a partir da RAIZ do projeto leitos-sus:
           python gerar_modelo_bi_sih.py
    3. As tabelas prontas vao aparecer em data/gold/, em formato .csv
       (para importar direto no Power BI) e .parquet.

Regras de negocio aplicadas (as mesmas dos notebooks 05 e 06):
    - Apenas AIH regular (IDENT igual a "1").
    - Periodo de 2021-01-01 a 2026-06-30, com base em DT_INTER.
    - Apenas internacoes respiratorias (DIAG_PRINC comecando com "J").

Este script usa SOMENTE a base do SIH (data/silver/sih_multianual.parquet).
Por isso, a dimensao de municipio traz apenas o codigo do municipio, sem
nome nem populacao (isso exigiria cruzar com a base do IBGE, que ficou
de fora por decisao do grupo).
"""

from pathlib import Path

import pandas as pd

# Caminhos (relativos a raiz do projeto)
ARQUIVO_SIH = Path("data/silver/sih_multianual.parquet")
PASTA_SAIDA = Path("data/gold")

INICIO_ANALISE = pd.Timestamp("2021-01-01")
FIM_ANALISE = pd.Timestamp("2026-06-30")


def carregar_sih() -> pd.DataFrame:
    if not ARQUIVO_SIH.exists():
        raise FileNotFoundError(
            f"Nao encontrei {ARQUIVO_SIH}. Rode este script a partir da raiz "
            "do projeto leitos-sus (onde fica a pasta data/)."
        )
    return pd.read_parquet(ARQUIVO_SIH)


def aplicar_regras_de_negocio(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["DT_INTER"] = pd.to_datetime(df["DT_INTER"])

    # Apenas AIH regular
    df = df[df["IDENT"] == "1"].copy()

    # Recorte temporal do projeto
    df = df[df["DT_INTER"].between(INICIO_ANALISE, FIM_ANALISE)].copy()

    # Padroniza municipios para 6 digitos, como no resto do projeto
    df["MUNIC_RES"] = df["MUNIC_RES"].astype("string").str.zfill(6)
    df["MUNIC_MOV"] = df["MUNIC_MOV"].astype("string").str.zfill(6)

    # Diagnostico principal como texto, e flag de internacao respiratoria
    df["DIAG_PRINC"] = df["DIAG_PRINC"].astype("string")
    df["RESPIRATORIO"] = df["DIAG_PRINC"].str.upper().str.startswith("J", na=False)

    # Filtra so as internacoes respiratorias, que sao o tema do painel
    df = df[df["RESPIRATORIO"]].copy()

    return df


def montar_fato(df: pd.DataFrame) -> pd.DataFrame:
    fato = df.copy()

    fato["ano_internacao"] = fato["DT_INTER"].dt.year
    fato["mes_internacao"] = fato["DT_INTER"].dt.month

    fato["indicador_obito"] = (fato["MORTE"].astype("string") == "1").astype("Int64")

    uti_numerico = pd.to_numeric(fato["UTI_MES_TO"], errors="coerce")
    fato["indicador_uti"] = (uti_numerico > 0).astype("Int64")

    fato["indicador_evasao"] = (fato["MUNIC_RES"] != fato["MUNIC_MOV"]).astype("Int64")

    fato["dias_permanencia"] = pd.to_numeric(fato["DIAS_PERM"], errors="coerce")

    fato["valor_total_aih"] = pd.to_numeric(fato["VAL_TOT"], errors="coerce")

    colunas_fato = [
        "N_AIH",
        "DT_INTER",
        "MUNIC_RES",
        "MUNIC_MOV",
        "DIAG_PRINC",
        "CNES",
        "dias_permanencia",
        "indicador_obito",
        "indicador_uti",
        "indicador_evasao",
        "valor_total_aih",
        "CAR_INT",
        "ESPEC",
    ]

    fato = fato[colunas_fato].rename(columns={
        "N_AIH": "chave_aih",
        "DT_INTER": "chave_tempo",
        "MUNIC_RES": "chave_municipio_residencia",
        "MUNIC_MOV": "chave_municipio_atendimento",
        "DIAG_PRINC": "chave_diagnostico",
        "CNES": "codigo_estabelecimento",
        "CAR_INT": "carater_internacao",
        "ESPEC": "especialidade",
    })

    return fato.reset_index(drop=True)


def montar_dim_tempo(df: pd.DataFrame) -> pd.DataFrame:
    datas = pd.DataFrame({"chave_tempo": df["DT_INTER"].drop_duplicates()})
    datas["ano"] = datas["chave_tempo"].dt.year
    datas["mes"] = datas["chave_tempo"].dt.month
    datas["trimestre"] = datas["chave_tempo"].dt.quarter
    return datas.sort_values("chave_tempo").reset_index(drop=True)


def montar_dim_diagnostico(df: pd.DataFrame) -> pd.DataFrame:
    diagnosticos = pd.DataFrame({
        "chave_diagnostico": df["DIAG_PRINC"].drop_duplicates().sort_values()
    })
    # Subgrupo por subcategoria (pneumonia, DPOC, asma, etc.) nao existe
    # ainda em nenhuma base do projeto. Fica como coluna vazia para o
    # grupo preencher manualmente depois, se quiser esse nivel de detalhe.
    diagnosticos["subgrupo_respiratorio"] = pd.NA
    return diagnosticos.reset_index(drop=True)


def montar_dim_municipio(df: pd.DataFrame) -> pd.DataFrame:
    codigos = pd.unique(pd.concat([df["MUNIC_RES"], df["MUNIC_MOV"]], ignore_index=True))
    dim = pd.DataFrame({"chave_municipio": sorted(codigos)})
    # Sem cruzar com a base de populacao do IBGE, so temos o codigo aqui.
    # Nome do municipio e populacao ficam de fora por decisao do grupo
    # (uso somente da base do SIH).
    return dim


def main() -> None:
    print("Carregando SIH consolidado...")
    df_bruto = carregar_sih()

    print("Aplicando regras de negocio e filtro de internacoes respiratorias...")
    df_respiratorio = aplicar_regras_de_negocio(df_bruto)
    print(f"Internacoes respiratorias no recorte: {len(df_respiratorio)}")

    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    tabelas = {
        "fato_internacoes_respiratorias": montar_fato(df_respiratorio),
        "dim_tempo": montar_dim_tempo(df_respiratorio),
        "dim_diagnostico": montar_dim_diagnostico(df_respiratorio),
        "dim_municipio": montar_dim_municipio(df_respiratorio),
    }

    for nome, tabela in tabelas.items():
        caminho_csv = PASTA_SAIDA / f"{nome}.csv"
        caminho_parquet = PASTA_SAIDA / f"{nome}.parquet"

        tabela.to_csv(caminho_csv, index=False, encoding="utf-8-sig")
        tabela.to_parquet(caminho_parquet, index=False)

        print(f"Gerado: {caminho_csv} ({len(tabela)} linhas)")

    print("\nPronto. As tabelas estao em data/gold/, prontas para importar no Power BI.")


if __name__ == "__main__":
    main()

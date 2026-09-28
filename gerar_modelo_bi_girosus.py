# -*- coding: utf-8 -*-
"""
Gera as tabelas do modelo de BI do produto GiroSUS, prontas para o Power BI.

GiroSUS: ocupação de leitos do SUS em Goiás, medida em leito-dia
(um paciente ocupando um leito por um dia), olhando todas as causas.
O desenho do modelo está em dashboard/GiroSUS_painel_ocupacao_leitos.pdf
(guia do analista) e os números batem com notebooks/06_analise_respiratoria.ipynb.

Como usar:
    1. Ative o ambiente virtual do projeto (.venv).
    2. Rode no terminal, na pasta do projeto:
           python gerar_modelo_bi_girosus.py
    3. As 8 tabelas aparecem em data/gold/girosus/, cada uma em .csv e em .parquet.
       Os .csv usam o padrão brasileiro (separador ";" e decimal ","), que o
       Excel e o Power BI em português leem direto.
       Atenção: os arquivos soltos em data/gold/ (sem a subpasta girosus)
       são do modelo respiratório antigo e NÃO são do painel.
    4. No fim, o script confere se as 8 tabelas e todas as colunas existem.
       Se faltar algo, ele para com ERRO e diz o que faltou.

Regras de negócio:
    - Só AIH regular (IDENT = "1"). As AIHs de continuação (IDENT = "5")
      são a mesma internação cobrada em partes.
    - Safra = ano da competência (ANO_CMPT). Todas as safras do projeto
      entram; o painel usa 2025 como padrão.
    - Tempo típico = mediana de DIAS_PERM do mesmo procedimento (PROC_REA)
      dentro da mesma safra.
    - Grupo de doença = capítulo da CID-10 pela primeira letra de DIAG_PRINC.

Fontes:
    - data/silver/sih_multianual.parquet (base do produto).
    - data/silver/populacao_multianual.parquet (só nomes de municípios).
    - data/raw/sih/<ano>/RDGO*.parquet (opcional, só para VAL_UTI, que ainda
      não está na silver). Sem esses arquivos, valor_uti fica vazio.
"""

from pathlib import Path

import numpy as np
import pandas as pd

# Caminhos a partir da pasta deste script: funciona de qualquer pasta do terminal.
RAIZ = Path(__file__).resolve().parent
ARQUIVO_SIH = RAIZ / "data/silver/sih_multianual.parquet"
ARQUIVO_POPULACAO = RAIZ / "data/silver/populacao_multianual.parquet"
PASTA_RAW_SIH = RAIZ / "data/raw/sih"
PASTA_SAIDA = RAIZ / "data/gold/girosus"

# O que precisa existir no fim: tabela -> colunas obrigatórias.
TABELAS_ESPERADAS = {
    "fato_internacoes": [
        "chave_aih", "safra", "competencia", "data_internacao", "data_saida", "cnes",
        "munic_residencia", "munic_atendimento", "cid", "proc_rea", "leito_dias",
        "tempo_tipico", "dias_acima_tipico", "faixa_duracao", "ordem_faixa",
        "fl_fora_municipio", "fl_uti", "dias_uti", "valor_pago", "valor_uti",
    ],
    "fato_ocupacao_diaria": ["cnes", "data", "grupo_doenca", "pacientes_internados", "entradas", "altas"],
    "dim_tempo": ["data", "ano", "mes", "nome_mes", "ano_mes", "trimestre", "dia_semana", "nome_dia", "fl_fim_semana"],
    "dim_diagnostico": ["cid", "capitulo", "grupo_doenca"],
    "dim_procedimento": ["proc_rea", "diagnostico_mais_comum", "tempo_tipico_2025", "nome_procedimento"],
    "dim_hospital": ["cnes", "municipio_atendimento", "nome_municipio", "nome_hospital"],
    "dim_municipio_residencia": ["codigo", "nome", "uf", "fl_goias"],
    "dim_municipio_atendimento": ["codigo", "nome", "uf", "fl_goias"],
}

INICIO_CALENDARIO = pd.Timestamp("2021-01-01")
FIM_CALENDARIO = pd.Timestamp("2026-06-30")

GRUPOS_CID = {
    "A": "Infecciosas", "B": "Infecciosas", "C": "Câncer",
    "E": "Endócrinas", "F": "Saúde mental", "G": "Sistema nervoso",
    "H": "Olho e ouvido", "I": "Circulatório", "J": "Respiratório",
    "K": "Digestivo", "L": "Pele", "M": "Osteomuscular",
    "N": "Geniturinário", "O": "Gravidez e parto", "P": "Perinatal",
    "Q": "Malformações", "R": "Sintomas mal definidos",
    "S": "Lesões e traumas", "T": "Lesões e traumas",
    "Z": "Contatos com serviço de saúde",
}

NOMES_MES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
NOMES_DIA = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]


def classificar_grupo(cid) -> str:
    if pd.isna(cid) or len(cid) == 0:
        return "Outros"
    letra = cid[0]
    if letra == "D":
        numero = cid[1:3]
        return "Câncer" if numero.isdigit() and int(numero) < 50 else "Sangue"
    return GRUPOS_CID.get(letra, "Outros")


def carregar_sih() -> pd.DataFrame:
    if not ARQUIVO_SIH.exists():
        raise FileNotFoundError(
            f"Nao encontrei {ARQUIVO_SIH}. A pasta data/silver precisa estar no projeto "
            "(ela vem do Git ou da promocao da staging)."
        )
    df = pd.read_parquet(ARQUIVO_SIH)
    return df[df["IDENT"].astype(str) == "1"].copy()


def carregar_valor_uti() -> pd.DataFrame | None:
    arquivos = sorted(PASTA_RAW_SIH.glob("*/RDGO*.parquet"))
    if not arquivos:
        print("Aviso: arquivos brutos do SIH nao encontrados; valor_uti ficara vazio.")
        return None
    partes = [
        pd.read_parquet(a, columns=["N_AIH", "IDENT", "ANO_CMPT", "MES_CMPT", "VAL_UTI"])
        for a in arquivos
    ]
    uti = pd.concat(partes, ignore_index=True)
    uti = uti[uti["IDENT"].astype(str) == "1"].drop(columns="IDENT")
    uti["VAL_UTI"] = pd.to_numeric(uti["VAL_UTI"], errors="coerce")
    return uti.drop_duplicates(subset=["N_AIH", "ANO_CMPT", "MES_CMPT"])


def nomes_municipios() -> pd.DataFrame:
    pop = pd.read_parquet(ARQUIVO_POPULACAO)
    pop = pop.sort_values("ano_referencia").drop_duplicates("codigo_ibge_7", keep="last")
    pop["codigo"] = pop["codigo_ibge_7"].astype(str).str[:6]
    return pop[["codigo", "municipio", "uf"]].drop_duplicates("codigo")


def montar_fato_internacoes(df: pd.DataFrame, uti: pd.DataFrame | None) -> pd.DataFrame:
    fato = pd.DataFrame({
        "chave_aih": df["N_AIH"].astype(str),
        "safra": df["ANO_CMPT"].astype(int),
        "competencia": pd.to_datetime(
            df["ANO_CMPT"].astype(str) + "-" + df["MES_CMPT"].astype(str).str.zfill(2) + "-01"
        ),
        "data_internacao": pd.to_datetime(df["DT_INTER"]),
        "data_saida": pd.to_datetime(df["DT_SAIDA"], format="%Y%m%d", errors="coerce"),
        "cnes": df["CNES"].astype(str).str.zfill(7),
        "munic_residencia": df["MUNIC_RES"].astype(str).str.zfill(6),
        "munic_atendimento": df["MUNIC_MOV"].astype(str).str.zfill(6),
        "cid": df["DIAG_PRINC"].astype(str).str.upper(),
        "proc_rea": df["PROC_REA"].astype(str),
        "leito_dias": pd.to_numeric(df["DIAS_PERM"], errors="coerce").fillna(0),
        "dias_uti": pd.to_numeric(df["UTI_MES_TO"], errors="coerce").fillna(0),
        "valor_pago": pd.to_numeric(df["VAL_TOT"], errors="coerce").fillna(0),
        "_ano": df["ANO_CMPT"].astype(str),
        "_mes": df["MES_CMPT"].astype(str),
    })

    fato["tempo_tipico"] = fato.groupby(["safra", "proc_rea"])["leito_dias"].transform("median")
    fato["dias_acima_tipico"] = (fato["leito_dias"] - fato["tempo_tipico"]).clip(lower=0)
    fato["faixa_duracao"] = pd.cut(
        fato["leito_dias"],
        bins=[-1, 0, 3, 7, 15, 30, np.inf],
        labels=["0 dia", "1–3", "4–7", "8–15", "16–30", "> 30"],
    ).astype(str)
    fato["ordem_faixa"] = fato["faixa_duracao"].map(
        {"0 dia": 1, "1–3": 2, "4–7": 3, "8–15": 4, "16–30": 5, "> 30": 6}
    )
    fato["fl_fora_municipio"] = (fato["munic_residencia"] != fato["munic_atendimento"]).astype(int)
    fato["fl_uti"] = (fato["dias_uti"] > 0).astype(int)

    if uti is not None:
        fato = fato.merge(
            uti.rename(columns={"N_AIH": "chave_aih", "ANO_CMPT": "_ano",
                                "MES_CMPT": "_mes", "VAL_UTI": "valor_uti"}),
            on=["chave_aih", "_ano", "_mes"], how="left",
        )
    else:
        fato["valor_uti"] = np.nan

    return fato.drop(columns=["_ano", "_mes"]).reset_index(drop=True)


def montar_fato_ocupacao(fato: pd.DataFrame, grupos: pd.Series) -> pd.DataFrame:
    """Uma linha por hospital x dia x grupo: pacientes internados, entradas e altas.

    Internado no dia d = entrou até d (data_internacao <= d) e ainda não saiu
    (data_saida > d). Usa todas as safras para incluir quem entrou antes.
    """
    base = fato[["cnes", "cid", "data_internacao", "data_saida"]].dropna().copy()
    base["grupo_doenca"] = base["cid"].map(grupos)

    inicio = base["data_internacao"].clip(lower=INICIO_CALENDARIO)
    fim = base["data_saida"].clip(upper=FIM_CALENDARIO + pd.Timedelta(days=1))
    dias = ((fim - inicio).dt.days).clip(lower=0).to_numpy()

    repeticoes = np.repeat(np.arange(len(base)), dias)
    deslocamento = np.arange(len(repeticoes)) - np.repeat(np.cumsum(dias) - dias, dias)
    datas = inicio.to_numpy()[repeticoes] + deslocamento.astype("timedelta64[D]")

    internados = pd.DataFrame({
        "cnes": base["cnes"].to_numpy()[repeticoes],
        "grupo_doenca": base["grupo_doenca"].to_numpy()[repeticoes],
        "data": datas,
    }).groupby(["cnes", "data", "grupo_doenca"]).size().rename("pacientes_internados")

    def contar(coluna, nome):
        x = base[base[coluna].between(INICIO_CALENDARIO, FIM_CALENDARIO)]
        return x.groupby(["cnes", coluna, "grupo_doenca"]).size().rename(nome).rename_axis(
            ["cnes", "data", "grupo_doenca"])

    ocupacao = pd.concat(
        [internados, contar("data_internacao", "entradas"), contar("data_saida", "altas")], axis=1
    ).fillna(0).astype(int).reset_index()
    return ocupacao


def montar_dim_tempo() -> pd.DataFrame:
    datas = pd.date_range(INICIO_CALENDARIO - pd.DateOffset(years=1), "2026-12-31", freq="D")
    dim = pd.DataFrame({"data": datas})
    dim["ano"] = dim["data"].dt.year
    dim["mes"] = dim["data"].dt.month
    dim["nome_mes"] = dim["mes"].map(lambda m: NOMES_MES[m - 1])
    dim["ano_mes"] = dim["data"].dt.strftime("%Y-%m")
    dim["trimestre"] = dim["data"].dt.quarter
    dim["dia_semana"] = dim["data"].dt.dayofweek + 1
    dim["nome_dia"] = dim["data"].dt.dayofweek.map(lambda d: NOMES_DIA[d])
    dim["fl_fim_semana"] = (dim["dia_semana"] >= 6).astype(int)
    return dim


def gravar(tabela: pd.DataFrame, caminho: Path, formato: str) -> None:
    try:
        if formato == "parquet":
            tabela.to_parquet(caminho, index=False)
        else:
            tabela.to_csv(caminho, index=False, encoding="utf-8-sig", sep=";", decimal=",")
    except PermissionError:
        raise SystemExit(
            f"\nERRO: nao consegui gravar {caminho.name}. O arquivo esta aberto em outro "
            "programa (Excel ou Power BI). Feche e rode o script de novo."
        )


def conferir_saida() -> None:
    """Confere se as 8 tabelas existem e têm todas as colunas. Para com erro se faltar algo."""
    problemas = []
    print("\nConferencia dos arquivos gerados:")
    for nome_tabela, colunas in TABELAS_ESPERADAS.items():
        caminho = PASTA_SAIDA / f"{nome_tabela}.parquet"
        if not (PASTA_SAIDA / f"{nome_tabela}.csv").exists():
            problemas.append(f"{nome_tabela}.csv nao foi gerado")
        if not caminho.exists():
            problemas.append(f"{nome_tabela}.parquet nao foi gerado")
            continue
        existentes = pd.read_parquet(caminho).columns
        faltando = [c for c in colunas if c not in existentes]
        if faltando:
            problemas.append(f"{nome_tabela}.parquet sem as colunas {faltando}")
        else:
            print(f"  OK  {nome_tabela} (.csv e .parquet, {len(colunas)} colunas)")
    if problemas:
        raise SystemExit("\nERRO na saida:\n  - " + "\n  - ".join(problemas))


def main() -> None:
    print(f"Gerando as tabelas do GiroSUS em: {PASTA_SAIDA}")
    print("Carregando SIH (AIH regular)...")
    df = carregar_sih()
    uti = carregar_valor_uti()

    print("Montando fato_internacoes...")
    fato = montar_fato_internacoes(df, uti)

    municipios = nomes_municipios()
    nome = dict(zip(municipios["codigo"], municipios["municipio"]))
    uf = dict(zip(municipios["codigo"], municipios["uf"]))

    dim_diagnostico = pd.DataFrame({"cid": fato["cid"].drop_duplicates().sort_values()})
    dim_diagnostico["capitulo"] = dim_diagnostico["cid"].str[0]
    dim_diagnostico["grupo_doenca"] = dim_diagnostico["cid"].map(classificar_grupo)
    grupos = dict(zip(dim_diagnostico["cid"], dim_diagnostico["grupo_doenca"]))

    codigos = pd.unique(pd.concat([fato["munic_residencia"], fato["munic_atendimento"]]))
    dim_municipio = pd.DataFrame({"codigo": sorted(codigos)})
    dim_municipio["nome"] = dim_municipio["codigo"].map(nome).fillna(dim_municipio["codigo"])
    dim_municipio["uf"] = dim_municipio["codigo"].map(uf)
    dim_municipio["fl_goias"] = dim_municipio["codigo"].str.startswith("52").astype(int)

    dim_hospital = (
        fato.groupby("cnes")["munic_atendimento"].agg(lambda s: s.mode().iloc[0])
        .rename("municipio_atendimento").reset_index()
    )
    dim_hospital["nome_municipio"] = dim_hospital["municipio_atendimento"].map(nome)
    dim_hospital["nome_hospital"] = ""  # preencher pela consulta pública do CNES

    safra_padrao = fato[fato["safra"] == 2025]
    dim_procedimento = fato.groupby("proc_rea").agg(
        diagnostico_mais_comum=("cid", lambda s: s.mode().iloc[0]),
    ).reset_index()
    dim_procedimento["tempo_tipico_2025"] = dim_procedimento["proc_rea"].map(
        safra_padrao.groupby("proc_rea")["leito_dias"].median()
    )
    dim_procedimento["nome_procedimento"] = ""  # preencher pela tabela SIGTAP

    print("Montando fato_ocupacao_diaria (pode levar alguns minutos)...")
    ocupacao = montar_fato_ocupacao(fato, grupos)

    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    tabelas = {
        "fato_internacoes": fato,
        "fato_ocupacao_diaria": ocupacao,
        "dim_tempo": montar_dim_tempo(),
        "dim_diagnostico": dim_diagnostico,
        "dim_procedimento": dim_procedimento,
        "dim_hospital": dim_hospital,
        "dim_municipio_residencia": dim_municipio,
        "dim_municipio_atendimento": dim_municipio,
    }
    for nome_tabela, tabela in tabelas.items():
        gravar(tabela, PASTA_SAIDA / f"{nome_tabela}.parquet", "parquet")
        gravar(tabela, PASTA_SAIDA / f"{nome_tabela}.csv", "csv")
        print(f"Gerado: {nome_tabela} ({len(tabela):,} linhas)")

    # Conferência com o material do produto (safra 2025)
    s = safra_padrao
    print("\nConferencia safra 2025 (deve bater com o PDF e o notebook 06):")
    print(f"  Internacoes:        {len(s):,}  (esperado 457.403)")
    print(f"  Leitos-dia:         {s['leito_dias'].sum():,.0f}  (esperado 1.835.227)")
    print(f"  Valor pago (R$ mi): {s['valor_pago'].sum() / 1e6:,.1f}  (esperado 726,1)")
    print(f"  % acima do tipico:  {s['dias_acima_tipico'].sum() / s['leito_dias'].sum() * 100:.1f}  (esperado 43,9)")
    conferir_saida()
    print(f"\nPronto. As 8 tabelas do Power BI estao em: {PASTA_SAIDA}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
Gera as tabelas do modelo de BI do produto GiroSUS, prontas para o Power BI.

GiroSUS: ocupação de leitos do SUS em Goiás, medida em leito-dia
(um paciente ocupando um leito por um dia), olhando todas as causas.

O script está alinhado com o PDF resumido dashboard/GiroSUS_painel_ocupacao_leitos.pdf
(11 páginas do painel). Cada tabela e coluna gerada alimenta um gráfico desse PDF:

    Pág. PDF  Seção do painel               O que usa
    1-3       Capa / O que você ganha /     cartões: leitos-dia, internações, permanência,
              Para que serve                valor pago, R$ por leito-dia; descobertas e ganho
    4         Como o SUS paga               faixa_pagamento (pneumonia sem UTI), valor_uti,
                                            dias_uti, diarias_acompanhante
    5         O que ocupa o leito           3 lentes por grupo_doenca, ranking de procedimentos
    6         Custo para o SUS              R$ por leito-dia por grupo, tabela, linha mensal
    7         Hospitais                     top 10 hospitais, % acima do típico, R$/dia
    8         Municípios                    rosca por município de atendimento, dependência
    9         Permanência além do típico    faixa_duracao, dias_acima_tipico, simulador
    10        Calendário de ocupação        fato_ocupacao_diaria: entradas/altas por dia da
                                            semana e variação mensal por grupo
    11        Sazonalidade                  sazonalidade_mensal: um mapa de calor mês × grupo
                                            de doença (internados por dia vs. média do ano)
    P29       Tendência                     tendencia_anual: média de internados por dia em cada
                                            ano de 2022 a 2025 (a rede cresce todo ano?)

Como usar:
    1. Ative o ambiente virtual do projeto (.venv).
    2. Rode no terminal, na pasta do projeto:
           python gerar_modelo_bi_girosus.py
    3. TUDO OLHA SÓ PARA A SAFRA 2025 (SAFRA_PADRAO), igual ao PDF:
       fato_internacoes e as dimensões têm só as internações da safra 2025, e
       fato_ocupacao_diaria tem só os dias de 2025. Para contar quem estava internado
       em 2025, a ocupação usa também as AIHs cobradas em 2024 e 2026 (quem entrou em
       dez/2025 só é cobrado em 2026); depois fica só com os dias de 2025.
       As 10 tabelas aparecem em data/gold/girosus/, todas em .csv (padrão brasileiro:
       separador ";" e decimal ","). Se houver .parquet antigos nessa pasta, o script
       apaga para não confundir.
       Para o Power BI, o script também grava data/gold/girosus/power_query/<tabela>.pq:
       uma consulta pronta por tabela, que já lê o ";" e o decimal "," (pt-BR) e já
       deixa os códigos (cnes, proc_rea, cid, codigo, munic_*) como Texto, sem perder
       o zero da frente. No Power BI: Obter dados > Consulta nula > Editor avançado,
       colar o conteúdo do .pq e renomear a consulta com o nome da tabela.
       Os nomes preenchidos à mão em dim_procedimento.nome_procedimento são
       PRESERVADOS entre uma execução e outra.
       HOSPITAL: o SIH não tem o nome do hospital. O hospital vem da coluna CNES do
       SIH (código do Cadastro Nacional de Estabelecimentos de Saúde, 7 dígitos).
       Os arquivos locais do CNES (LTGO*, leitos) também não têm o nome. Por isso
       dim_hospital identifica o hospital pelo cnes e pelo município e NÃO tem
       nome_hospital: essa coluna sairia vazia. A conferência para com ERRO se ela aparecer.
    4. No fim, o script faz duas conferências:
       a) estrutura: as 10 tabelas e todas as colunas existem e NENHUM valor está vazio
          (qualquer célula vazia, em qualquer coluna, para o script com ERRO);
       b) números: recalcula cada número do PDF (safra 2025) a partir das tabelas
          geradas, do mesmo jeito que as medidas DAX calculam.
       Se algo não bater, ele para com ERRO e lista o que divergiu.

Regras de negócio:
    - Só AIH regular (IDENT = "1"). As AIHs de continuação (IDENT = "5")
      são a mesma internação cobrada em partes.
    - Safra = ano da competência (ANO_CMPT). Só a safra 2025 entra nas tabelas.
    - Tempo típico = mediana de DIAS_PERM do mesmo procedimento (PROC_REA)
      dentro da mesma safra.
    - Grupo de doença = capítulo da CID-10 pela primeira letra de DIAG_PRINC.

Fontes:
    - data/silver/sih_multianual.parquet (base do produto).
    - data/silver/populacao_multianual.parquet (só nomes de municípios).
    - data/raw/sih/<ano>/RDGO*.parquet (VAL_UTI e DIAR_ACOM, que ainda não estão
      na silver; usados na pág. 4 do PDF). Sem esses arquivos o script para com ERRO,
      em vez de gerar as colunas vazias.
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
PASTA_POWER_QUERY = PASTA_SAIDA / "power_query"

# Códigos que o Power BI precisa ler como Texto (senão "0965324" vira 965324).
COLUNAS_CODIGO = {"cnes", "proc_rea", "cid", "codigo", "munic_residencia", "munic_atendimento",
                  "chave_aih", "diagnostico_mais_comum", "capitulo", "uf"}

SAFRA_PADRAO = 2025

# O que precisa existir no fim: tabela -> colunas obrigatórias.
TABELAS_ESPERADAS = {
    "fato_internacoes": [
        "chave_aih", "safra", "competencia", "data_internacao", "data_saida", "cnes",
        "munic_residencia", "munic_atendimento", "cid", "proc_rea", "leito_dias",
        "tempo_tipico", "dias_acima_tipico", "faixa_duracao", "ordem_faixa",
        "faixa_pagamento", "ordem_faixa_pagamento", "fl_permanencia_longa",
        "fl_fora_municipio", "fl_uti", "dias_uti", "valor_pago", "valor_uti",
        "diarias_acompanhante", "fl_acompanhante",
    ],
    "fato_ocupacao_diaria": ["cnes", "data", "grupo_doenca", "pacientes_internados", "entradas", "altas"],
    "dim_tempo": ["data", "ano", "mes", "nome_mes", "ano_mes", "dia_semana", "nome_dia", "fl_fim_semana"],
    "dim_diagnostico": ["cid", "capitulo", "grupo_doenca"],
    "dim_procedimento": ["proc_rea", "diagnostico_mais_comum", "tempo_tipico_2025", "nome_procedimento"],
    # Sem nome_hospital: o SIH só tem o código CNES do hospital, não o nome.
    "dim_hospital": ["cnes", "municipio_atendimento", "nome_municipio"],
    "dim_municipio_residencia": ["codigo", "nome", "uf", "fl_goias"],
    "dim_municipio_atendimento": ["codigo", "nome", "uf", "fl_goias"],
    # Tabela de apoio (sem relacionamento): um gráfico de sazonalidade, mês × grupo de doença.
    "sazonalidade_mensal": ["mes", "nome_mes", "grupo_doenca", "fl_total", "internados_dia",
                            "media_ano", "variacao_pct", "fl_pico", "fl_vale"],
    # Tabela de apoio (sem relacionamento): tendência da rede, um ano por linha.
    "tendencia_anual": ["ano", "internados_dia", "fl_ano_painel"],
}

# Ocupação diária: só os dias de 2025 (01/01/2025 a 31/12/2025).
INICIO_CALENDARIO = pd.Timestamp(f"{SAFRA_PADRAO}-01-01")
FIM_CALENDARIO = pd.Timestamp(f"{SAFRA_PADRAO}-12-31")

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

# Pág. 5 do PDF (ranking de procedimentos) e pág. 4 (pneumonia / saúde mental).
# Nome pelo diagnóstico principal mais comum; conferir o nome oficial no SIGTAP.
# Nomes preenchidos à mão no dim_procedimento.csv têm prioridade sobre estes.
NOMES_PROCEDIMENTO = {
    "0303140151": "Pneumonia ou gripe",
    "0303010037": "Infecções bacterianas / sepse",
    "0415010012": "Cirurgias múltiplas",
    "0303170190": "Psiquiatria (curta permanência)",
    "0411010034": "Parto cesariano",
    "0303060212": "Insuficiência cardíaca",
    "0303040149": "AVC",
    "0303150050": "Infecção urinária",
}
# Procedimento sem nome (nem no código, nem preenchido à mão): nenhuma base local
# (SIH, CNES, IBGE) tem o nome do procedimento, então ele aparece pelo próprio código.
ROTULO_PROCEDIMENTO = "Procedimento"
PROC_PNEUMONIA = "0303140151"
PROC_PSIQUIATRIA = "0303170190"

# Pág. 9: quem fica pouco e quem fica muito.
FAIXAS_DURACAO = ([-1, 0, 3, 7, 15, 30, np.inf], ["0 dia", "1–3", "4–7", "8–15", "16–30", "> 30"])
# Pág. 4: pacote pago x dias internado (0 dia entra junto com 1 a 2 dias).
FAIXAS_PAGAMENTO = ([-1, 2, 4, 7, 14, np.inf], ["1–2 dias", "3–4 dias", "5–7 dias", "8–14 dias", "15+ dias"])

# P29: anos da tendência. 2021 fica de fora: quem já estava internado em jan/2021
# entrou em 2020, antes da base, e o começo de 2021 sairia baixo demais.
ANOS_TENDENCIA = range(2022, SAFRA_PADRAO + 1)

# Pág. 11: linha com a rede inteira na tabela de sazonalidade (fl_total = 1).
ROTULO_TOTAL_SAZONALIDADE = "Total da rede"

NOMES_MES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
NOMES_DIA = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]


# Leitura

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


def carregar_complementos_raw() -> pd.DataFrame | None:
    """VAL_UTI e DIAR_ACOM vêm do SIH bruto (ainda não estão na silver)."""
    arquivos = sorted(PASTA_RAW_SIH.glob("*/RDGO*.parquet"))
    if not arquivos:
        raise SystemExit(
            f"\nERRO: arquivos brutos do SIH nao encontrados em {PASTA_RAW_SIH}. Sem eles, valor_uti e "
            "diarias_acompanhante ficariam vazios. Converta os .dbc com python -m src.converter_dbc."
        )
    colunas = ["N_AIH", "IDENT", "ANO_CMPT", "MES_CMPT", "VAL_UTI", "DIAR_ACOM"]
    raw = pd.concat([pd.read_parquet(a, columns=colunas) for a in arquivos], ignore_index=True)
    raw = raw[raw["IDENT"].astype(str) == "1"].drop(columns="IDENT")
    raw["VAL_UTI"] = pd.to_numeric(raw["VAL_UTI"], errors="coerce")
    raw["DIAR_ACOM"] = pd.to_numeric(raw["DIAR_ACOM"], errors="coerce")
    for c in ["N_AIH", "ANO_CMPT", "MES_CMPT"]:
        raw[c] = raw[c].astype(str)
    return raw.drop_duplicates(subset=["N_AIH", "ANO_CMPT", "MES_CMPT"])


def nomes_municipios() -> pd.DataFrame:
    pop = pd.read_parquet(ARQUIVO_POPULACAO)
    pop = pop.sort_values("ano_referencia").drop_duplicates("codigo_ibge_7", keep="last")
    pop["codigo"] = pop["codigo_ibge_7"].astype(str).str[:6]
    return pop[["codigo", "municipio", "uf"]].drop_duplicates("codigo")


def ler_nomes_manuais(tabela: str, chave: str, coluna: str) -> dict:
    """Lê os nomes já preenchidos à mão no .csv anterior, para não perder o trabalho."""
    caminho = PASTA_SAIDA / f"{tabela}.csv"
    if not caminho.exists():
        return {}
    antigo = pd.read_csv(caminho, sep=";", dtype=str, encoding="utf-8-sig", keep_default_na=False)
    if chave not in antigo or coluna not in antigo:
        return {}
    antigo = antigo[antigo[coluna].str.strip() != ""]
    if coluna == "nome_procedimento":  # rótulo automático ("Procedimento <código>") não é nome manual
        antigo = antigo[antigo[coluna] != ROTULO_PROCEDIMENTO + " " + antigo[chave]]
    return dict(zip(antigo[chave], antigo[coluna]))


# Tabelas

def montar_fato_internacoes(df: pd.DataFrame, raw: pd.DataFrame | None) -> pd.DataFrame:
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

    # Pág. 9: tempo típico, dias acima e faixas de duração
    fato["tempo_tipico"] = fato.groupby(["safra", "proc_rea"])["leito_dias"].transform("median")
    fato["dias_acima_tipico"] = (fato["leito_dias"] - fato["tempo_tipico"]).clip(lower=0)
    bins, rotulos = FAIXAS_DURACAO
    fato["faixa_duracao"] = pd.cut(fato["leito_dias"], bins=bins, labels=rotulos).astype(str)
    fato["ordem_faixa"] = fato["faixa_duracao"].map({r: i + 1 for i, r in enumerate(rotulos)})
    fato["fl_permanencia_longa"] = (fato["leito_dias"] > 15).astype(int)

    # Pág. 4: pacote pago x dias internado
    bins, rotulos = FAIXAS_PAGAMENTO
    fato["faixa_pagamento"] = pd.cut(fato["leito_dias"], bins=bins, labels=rotulos).astype(str)
    fato["ordem_faixa_pagamento"] = fato["faixa_pagamento"].map({r: i + 1 for i, r in enumerate(rotulos)})

    # Pág. 8: dependência de outra cidade
    fato["fl_fora_municipio"] = (fato["munic_residencia"] != fato["munic_atendimento"]).astype(int)
    fato["fl_uti"] = (fato["dias_uti"] > 0).astype(int)

    # Pág. 4: UTI e acompanhante (SIH bruto)
    if raw is not None:
        fato = fato.merge(
            raw.rename(columns={"N_AIH": "chave_aih", "ANO_CMPT": "_ano", "MES_CMPT": "_mes",
                                "VAL_UTI": "valor_uti", "DIAR_ACOM": "diarias_acompanhante"}),
            on=["chave_aih", "_ano", "_mes"], how="left",
        )
    else:
        fato["valor_uti"] = np.nan
        fato["diarias_acompanhante"] = np.nan
    fato["fl_acompanhante"] = (fato["diarias_acompanhante"].fillna(0) > 0).astype(int)

    return fato.drop(columns=["_ano", "_mes"]).reset_index(drop=True)


def montar_fato_ocupacao(fato: pd.DataFrame, grupos: dict) -> pd.DataFrame:
    """Pág. 10: uma linha por hospital x dia x grupo: pacientes internados, entradas e altas.

    Internado no dia d = entrou até d (data_internacao <= d) e ainda não saiu
    (data_saida > d). Recebe as AIHs de todas as safras só para contar quem estava
    internado nos dias de 2025 (quem entrou em dez/2025 é cobrado em 2026).
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

    return pd.concat(
        [internados, contar("data_internacao", "entradas"), contar("data_saida", "altas")], axis=1
    ).fillna(0).astype(int).reset_index()


def montar_dim_tempo(fato: pd.DataFrame) -> pd.DataFrame:
    """Calendário da 1ª data de internação da safra 2025 (17/05/2024) até 31/12/2025.

    Começa antes de 2025 só para ligar as AIHs cobradas em 2025 de quem entrou em 2024.
    """
    datas = pd.date_range(fato["data_internacao"].min().normalize(), FIM_CALENDARIO, freq="D")
    dim = pd.DataFrame({"data": datas})
    dim["ano"] = dim["data"].dt.year
    dim["mes"] = dim["data"].dt.month
    dim["nome_mes"] = dim["mes"].map(lambda m: NOMES_MES[m - 1])
    dim["ano_mes"] = dim["data"].dt.strftime("%Y-%m")
    dim["dia_semana"] = dim["data"].dt.dayofweek + 1
    dim["nome_dia"] = dim["data"].dt.dayofweek.map(lambda d: NOMES_DIA[d])
    dim["fl_fim_semana"] = (dim["dia_semana"] >= 6).astype(int)
    return dim


def montar_dim_diagnostico(fato: pd.DataFrame) -> pd.DataFrame:
    dim = pd.DataFrame({"cid": fato["cid"].drop_duplicates().sort_values()})
    dim["capitulo"] = dim["cid"].str[0]
    dim["grupo_doenca"] = dim["cid"].map(classificar_grupo)
    return dim.reset_index(drop=True)


def montar_dim_municipio(fato: pd.DataFrame, municipios: pd.DataFrame) -> pd.DataFrame:
    nome = dict(zip(municipios["codigo"], municipios["municipio"]))
    uf = dict(zip(municipios["codigo"], municipios["uf"]))
    codigos = pd.unique(pd.concat([fato["munic_residencia"], fato["munic_atendimento"]]))
    dim = pd.DataFrame({"codigo": sorted(codigos)})
    dim["nome"] = dim["codigo"].map(nome).fillna(dim["codigo"])
    dim["uf"] = dim["codigo"].map(uf)
    dim["fl_goias"] = dim["codigo"].str.startswith("52").astype(int)
    return dim


def montar_dim_hospital(fato: pd.DataFrame, municipios: pd.DataFrame) -> pd.DataFrame:
    # cnes vem da coluna CNES do SIH (código do estabelecimento no CNES).
    # O SIH não tem o nome do hospital: não criar nome_hospital (sairia vazio).
    nome = dict(zip(municipios["codigo"], municipios["municipio"]))
    dim = (
        fato.groupby("cnes")["munic_atendimento"].agg(lambda s: s.mode().iloc[0])
        .rename("municipio_atendimento").reset_index()
    )
    dim["nome_municipio"] = dim["municipio_atendimento"].map(nome)
    return dim


def montar_sazonalidade(ocupacao: pd.DataFrame) -> pd.DataFrame:
    """Pág. 11: sazonalidade de 2025, uma linha por mês × grupo de doença (+ total da rede).

    internados_dia = média de pacientes internados por dia no mês (todos os dias de 2025,
    inclusive os dias sem paciente do grupo, que contam como 0). variacao_pct compara o mês
    com a média do ano do mesmo grupo (0 = mês igual à média). Mesma base da pág. 10.
    """
    dias = pd.date_range(INICIO_CALENDARIO, FIM_CALENDARIO, freq="D")
    por_dia = (ocupacao.groupby(["data", "grupo_doenca"])["pacientes_internados"].sum()
               .unstack(fill_value=0).reindex(dias, fill_value=0))
    por_dia[ROTULO_TOTAL_SAZONALIDADE] = por_dia.sum(axis=1)
    mensal = por_dia.groupby(por_dia.index.month).mean()
    mensal = mensal.loc[:, mensal.mean() > 0]  # grupo sem nenhum internado não tem média
    linhas = mensal.rename_axis("mes").reset_index().melt(
        id_vars="mes", var_name="grupo_doenca", value_name="internados_dia")
    linhas["media_ano"] = linhas.groupby("grupo_doenca")["internados_dia"].transform("mean")
    linhas["variacao_pct"] = (linhas["internados_dia"] / linhas["media_ano"] - 1) * 100
    linhas["fl_pico"] = (linhas["internados_dia"]
                         == linhas.groupby("grupo_doenca")["internados_dia"].transform("max")).astype(int)
    linhas["fl_vale"] = (linhas["internados_dia"]
                         == linhas.groupby("grupo_doenca")["internados_dia"].transform("min")).astype(int)
    linhas["fl_total"] = (linhas["grupo_doenca"] == ROTULO_TOTAL_SAZONALIDADE).astype(int)
    linhas["nome_mes"] = linhas["mes"].map(lambda m: NOMES_MES[m - 1])
    for c in ["internados_dia", "media_ano", "variacao_pct"]:
        linhas[c] = linhas[c].round(1)
    linhas = linhas.sort_values(["fl_total", "media_ano", "mes"], ascending=[False, False, True])
    return linhas[TABELAS_ESPERADAS["sazonalidade_mensal"]].reset_index(drop=True)


def montar_tendencia(todas_safras: pd.DataFrame) -> pd.DataFrame:
    """P29: a rede cresce todo ano? Média de pacientes internados por dia, ano a ano.

    Mesma regra da ocupação diária (internado no dia = entrou até o dia e ainda não saiu),
    com as AIHs de todas as safras. O valor do ano é a média das 12 médias mensais,
    igual à media_ano do "Total da rede" na sazonalidade_mensal (2025 = mesmo número).
    """
    inicio = pd.Timestamp(f"{ANOS_TENDENCIA[0]}-01-01")
    fim = pd.Timestamp(f"{ANOS_TENDENCIA[-1]}-12-31")
    base = todas_safras[["data_internacao", "data_saida"]].dropna()
    entrada = base["data_internacao"].clip(lower=inicio)
    saida = base["data_saida"].clip(upper=fim + pd.Timedelta(days=1))
    dias = ((saida - entrada).dt.days).clip(lower=0).to_numpy()
    repeticoes = np.repeat(np.arange(len(base)), dias)
    deslocamento = np.arange(len(repeticoes)) - np.repeat(np.cumsum(dias) - dias, dias)
    datas = entrada.to_numpy()[repeticoes] + deslocamento.astype("timedelta64[D]")
    por_dia = (pd.Series(1, index=pd.DatetimeIndex(datas)).groupby(level=0).size()
               .reindex(pd.date_range(inicio, fim, freq="D"), fill_value=0))
    mensal = por_dia.groupby([por_dia.index.year, por_dia.index.month]).mean()
    anual = mensal.groupby(level=0).mean().round(1)
    dim = pd.DataFrame({"ano": anual.index.astype(int), "internados_dia": anual.to_numpy()})
    dim["fl_ano_painel"] = (dim["ano"] == SAFRA_PADRAO).astype(int)
    return dim


def montar_dim_procedimento(fato: pd.DataFrame) -> pd.DataFrame:
    safra = fato[fato["safra"] == SAFRA_PADRAO]
    dim = fato.groupby("proc_rea").agg(
        diagnostico_mais_comum=("cid", lambda s: s.mode().iloc[0]),
    ).reset_index()
    dim["tempo_tipico_2025"] = dim["proc_rea"].map(safra.groupby("proc_rea")["leito_dias"].median())
    manuais = ler_nomes_manuais("dim_procedimento", "proc_rea", "nome_procedimento")
    nomes = {**NOMES_PROCEDIMENTO, **manuais}  # o que foi preenchido à mão tem prioridade
    # Demais: rótulo com o código (substitua à mão pelo nome da tabela SIGTAP, se quiser).
    dim["nome_procedimento"] = dim["proc_rea"].map(nomes).fillna(ROTULO_PROCEDIMENTO + " " + dim["proc_rea"])
    return dim


# Gravação

def gravar(tabela: pd.DataFrame, caminho: Path) -> None:
    try:
        tabela.to_csv(caminho, index=False, encoding="utf-8-sig", sep=";", decimal=",")
    except PermissionError:
        raise SystemExit(
            f"\nERRO: nao consegui gravar {caminho.name}. O arquivo esta aberto em outro "
            "programa (Excel ou Power BI). Feche e rode o script de novo."
        )


def tipo_power_query(coluna: str, serie: pd.Series) -> str:
    """Tipo do Power Query para cada coluna: códigos sempre Texto."""
    if coluna in COLUNAS_CODIGO:
        return "type text"
    if pd.api.types.is_datetime64_any_dtype(serie):
        return "type date"
    if pd.api.types.is_integer_dtype(serie):
        return "Int64.Type"
    if pd.api.types.is_float_dtype(serie):
        return "type number"
    return "type text"


def gravar_power_query(nome_tabela: str, tabela: pd.DataFrame) -> None:
    """Consulta pronta para colar no Power BI: lê ";" e decimal "," (pt-BR) e deixa os códigos como Texto."""
    tipos = ",\n        ".join(
        f'{{"{c}", {tipo_power_query(c, tabela[c])}}}' for c in tabela.columns
    )
    consulta = f"""// {nome_tabela}: cole em Obter dados > Consulta nula > Editor avançado
// e renomeie a consulta para {nome_tabela}. Se mudar a pasta do projeto, ajuste Arquivo.
let
    Arquivo = "{PASTA_SAIDA / f"{nome_tabela}.csv"}",
    Fonte = Csv.Document(File.Contents(Arquivo), [Delimiter = ";", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    // Códigos como Texto (mantém o zero da frente); números com decimal "," (pt-BR)
    Tipos = Table.TransformColumnTypes(Cabecalho, {{
        {tipos}
    }}, "pt-BR")
in
    Tipos
"""
    PASTA_POWER_QUERY.mkdir(parents=True, exist_ok=True)
    (PASTA_POWER_QUERY / f"{nome_tabela}.pq").write_text(consulta, encoding="utf-8")


def conferir_saida() -> None:
    """Estrutura: as 10 tabelas existem, têm todas as colunas e nada essencial está vazio."""
    problemas = []
    print("\nConferencia dos arquivos gerados:")
    for nome_tabela, colunas in TABELAS_ESPERADAS.items():
        caminho = PASTA_SAIDA / f"{nome_tabela}.csv"
        if not caminho.exists():
            problemas.append(f"{nome_tabela}.csv nao foi gerado")
            continue
        existentes = pd.read_csv(caminho, sep=";", nrows=0, encoding="utf-8-sig").columns
        faltando = [c for c in colunas if c not in existentes]
        if faltando:
            problemas.append(f"{nome_tabela}.csv sem as colunas {faltando}")
            continue
        # Nenhum valor vazio, em nenhuma coluna (não só colunas 100% vazias).
        dados = pd.read_csv(caminho, sep=";", encoding="utf-8-sig", dtype=str, keep_default_na=False)
        if dados.empty:
            problemas.append(f"{nome_tabela}.csv esta sem linhas")
        vazias = {c: int(n) for c, n in (dados.apply(lambda s: s.str.strip() == "").sum()).items() if n}
        if vazias:
            problemas.append(f"{nome_tabela}.csv com valores vazios (coluna: quantidade): {vazias}")
        else:
            print(f"  OK  {nome_tabela}.csv ({len(colunas)} colunas)")
    hospital = PASTA_SAIDA / "dim_hospital.csv"
    if hospital.exists() and "nome_hospital" in pd.read_csv(hospital, sep=";", nrows=0, encoding="utf-8-sig").columns:
        problemas.append("dim_hospital.csv tem nome_hospital, mas o SIH nao tem o nome do hospital (so o codigo CNES)")
    sobras = sorted(p.name for p in PASTA_SAIDA.glob("*.parquet"))
    if sobras:
        problemas.append(f"ainda ha .parquet na pasta: {sobras}")
    if problemas:
        raise SystemExit("\nERRO na saida:\n  - " + "\n  - ".join(problemas))


# Conferência do PDF

def _pct(parte, total) -> float:
    return parte / total * 100 if total else float("nan")


def calcular_numeros_pdf(fato, ocupacao, dim_diag, dim_hosp, dim_mun, sazonalidade, tendencia) -> list[tuple]:
    """Recalcula, a partir das tabelas geradas, cada número do PDF (safra 2025).

    Devolve (pág., descrição, valor calculado, esperado, tolerância, depende_da_ocupacao).
    Os cálculos imitam as medidas DAX do guia (filtros de página: safra = 2025).
    """
    s = fato[fato["safra"] == SAFRA_PADRAO].merge(dim_diag[["cid", "grupo_doenca"]], on="cid", how="left")
    nome_mun = dict(zip(dim_mun["codigo"], dim_mun["nome"]))
    ld, n, vp = s["leito_dias"].sum(), len(s), s["valor_pago"].sum()
    acima = s["dias_acima_tipico"].sum()
    r = []

    def add(pag, desc, valor, esperado, tol, ocup=False):
        r.append((pag, desc, float(valor), float(esperado), tol, ocup))

    # Págs. 1-3: cartões, descobertas e ganho
    add("1-3", "Leitos-dia", ld, 1_835_227, 0)
    add("1-3", "Internacoes", n, 457_403, 0)
    add("1-3", "Permanencia media (dias)", ld / n, 4.0, 0.05)
    add("1-3", "Valor pago (R$ mi)", vp / 1e6, 726.1, 0.05)
    add("1-3", "R$ por leito-dia", vp / ld, 396, 0.5)
    g = s.groupby("grupo_doenca").agg(n=("cid", "size"), ld=("leito_dias", "sum"), vp=("valor_pago", "sum"),
                                      ac=("dias_acima_tipico", "sum"))
    add("1-3", "Respiratorio % leitos-dia", _pct(g.loc["Respiratório", "ld"], ld), 12.5, 0.05)
    add("1-3", "Respiratorio % valor", _pct(g.loc["Respiratório", "vp"], vp), 8.9, 0.05)
    add("1-3", "Circulatorio % leitos-dia", _pct(g.loc["Circulatório", "ld"], ld), 11.9, 0.05)
    add("1-3", "Circulatorio % valor", _pct(g.loc["Circulatório", "vp"], vp), 21.0, 0.05)
    longa = s[s["fl_permanencia_longa"] == 1]
    add("1-3", "Internacoes > 15 dias: % internacoes", _pct(len(longa), n), 4.4, 0.05)
    add("1-3", "Internacoes > 15 dias: % leitos-dia", _pct(longa["leito_dias"].sum(), ld), 27.3, 0.05)
    gyn = s[s["munic_atendimento"] == "520870"]
    add("1-3", "Goiania: % dos leitos-dia do estado", _pct(gyn["leito_dias"].sum(), ld), 44.7, 0.05)
    add("1-3", "Goiania: % leitos-dia de quem mora fora",
        _pct(gyn.loc[gyn["fl_fora_municipio"] == 1, "leito_dias"].sum(), gyn["leito_dias"].sum()), 56.6, 0.05)
    add("1-3", "Simulador 10%: leitos-dia liberados (mil)", acima * 0.10 / 1e3, 80.6, 0.05)
    add("1-3", "Simulador 10%: internacoes a mais (mil)", acima * 0.10 / (ld / n) / 1e3, 20.0, 0.5)

    # Pág. 4: como o SUS paga
    pn = s[(s["proc_rea"] == PROC_PNEUMONIA) & (s["fl_uti"] == 0)].groupby("faixa_pagamento").agg(
        v=("valor_pago", "mean"), vs=("valor_pago", "sum"), d=("leito_dias", "sum"))
    for faixa, v_esp, dia_esp in [("1–2 dias", 606, 377), ("3–4 dias", 626, 183), ("5–7 dias", 684, 117),
                                  ("8–14 dias", 839, 84), ("15+ dias", 1451, 64)]:
        add("4", f"Pneumonia sem UTI {faixa}: valor medio (R$)", pn.loc[faixa, "v"], v_esp, 0.51)
        add("4", f"Pneumonia sem UTI {faixa}: R$ por dia", pn.loc[faixa, "vs"] / pn.loc[faixa, "d"], dia_esp, 0.5)
    add("4", "R$ por dia de UTI", s["valor_uti"].sum() / s["dias_uti"].sum(), 631, 0.5)
    add("4", "Valor UTI (R$ mi)", s["valor_uti"].sum() / 1e6, 176, 0.5)
    add("4", "UTI % do valor pago", _pct(s["valor_uti"].sum(), vp), 24, 0.5)
    psi = s[s["proc_rea"] == PROC_PSIQUIATRIA]
    add("4", "Saude mental (psiquiatria): R$ por dia", psi["valor_pago"].sum() / psi["leito_dias"].sum(), 82, 0.5)
    add("4", "% internacoes com diaria de acompanhante", _pct(s["fl_acompanhante"].sum(), n), 52, 0.5)

    # Pág. 5: três lentes por grupo e ranking de procedimentos
    lentes = {  # grupo: (% internações, % leitos-dia, % custo)
        "Lesões e traumas": (15.8, 15.8, 13.4), "Respiratório": (10.0, 12.5, 8.9),
        "Circulatório": (9.6, 11.9, 21.0), "Infecciosas": (5.6, 8.5, 5.9),
        "Digestivo": (10.2, 8.3, 7.3), "Gravidez e parto": (13.0, 7.9, 4.8),
        "Geniturinário": (7.8, 7.3, 6.4), "Câncer": (5.9, 5.1, 10.8),
        "Saúde mental": (2.1, 5.0, 0.9), "Perinatal": (2.3, 4.2, 4.1),
    }
    for grupo, (p_n, p_ld, p_vp) in lentes.items():
        add("5", f"{grupo}: % internacoes", _pct(g.loc[grupo, "n"], n), p_n, 0.05)
        add("5", f"{grupo}: % leitos-dia", _pct(g.loc[grupo, "ld"], ld), p_ld, 0.05)
        add("5", f"{grupo}: % custo", _pct(g.loc[grupo, "vp"], vp), p_vp, 0.05)
    proc = s.groupby("proc_rea")["leito_dias"].sum()
    for cod, esperado in [("0303140151", 143_480), ("0303010037", 84_876), ("0415010012", 83_371),
                          ("0303170190", 56_512), ("0411010034", 49_070), ("0303060212", 39_109),
                          ("0303040149", 36_326), ("0303150050", 35_430)]:
        add("5", f"Procedimento {NOMES_PROCEDIMENTO[cod]}: leitos-dia", proc.get(cod, 0), esperado, 0)
    add("5", "Top 8 procedimentos na ordem do PDF",
        list(proc.nlargest(8).index) == list(NOMES_PROCEDIMENTO), 1, 0)

    # Pág. 6: custo para o SUS
    rs = (g["vp"] / g["ld"])
    for grupo, esperado in [("Saúde mental", 69), ("Pele", 132), ("Gravidez e parto", 241), ("Infecciosas", 275),
                            ("Respiratório", 281), ("Endócrinas", 289), ("Sistema nervoso", 298),
                            ("Sintomas mal definidos", 322), ("Lesões e traumas", 336), ("Geniturinário", 348),
                            ("Digestivo", 350), ("Perinatal", 393), ("Circulatório", 699), ("Câncer", 831),
                            ("Malformações", 878), ("Osteomuscular", 1040)]:
        add("6", f"{grupo}: R$ por leito-dia", rs[grupo], esperado, 0.5)
    for grupo, esperado in [("Circulatório", 152.8), ("Lesões e traumas", 97.6), ("Câncer", 78.1)]:
        add("6", f"{grupo}: valor pago (R$ mi)", g.loc[grupo, "vp"] / 1e6, esperado, 0.05)
    for grupo, esperado in [("Malformações", 4416), ("Osteomuscular", 3567), ("Circulatório", 3479)]:
        add("6", f"{grupo}: R$ por internacao", g.loc[grupo, "vp"] / g.loc[grupo, "n"], esperado, 0.5)
    mensal = s.groupby(s["competencia"].dt.month)["valor_pago"].sum() / 1e6
    add("6", "Menor mes de gasto: fev (R$ mi)", mensal.loc[2], 55.9, 0.05)
    add("6", "Maior mes de gasto: jul (R$ mi)", mensal.loc[7], 64.6, 0.05)
    add("6", "Fev e jul sao o menor e o maior mes", mensal.idxmin() == 2 and mensal.idxmax() == 7, 1, 0)

    # Pág. 7: hospitais
    h = s.groupby("cnes").agg(ld=("leito_dias", "sum"), vp=("valor_pago", "sum"), ac=("dias_acima_tipico", "sum"),
                              n=("cid", "size"))
    top = h.nlargest(10, "ld")
    esperado_top = {  # cnes: (mil leitos-dia, % acima, R$/dia)
        "7743068": (148.5, 52, 509), "2338262": (120.6, 56, 298), "0547484": (90.2, 54, 260),
        "2338424": (64.9, 56, 389), "9680977": (59.2, 52, 480), "2339196": (47.9, 50, 288),
        "2338734": (47.6, 55, 479), "2506815": (45.0, 36, 1038), "0965324": (44.5, 56, 307),
        "2338351": (42.7, 53, 615),
    }
    add("7", "Top 10 hospitais = os do PDF", set(top.index) == set(esperado_top), 1, 0)
    for cnes, (mil, pct_ac, rs_dia) in esperado_top.items():
        if cnes not in h.index:
            add("7", f"Hospital {cnes} existe na base", 0, 1, 0)
            continue
        add("7", f"Hospital {cnes}: mil leitos-dia", h.loc[cnes, "ld"] / 1e3, mil, 0.05)
        add("7", f"Hospital {cnes}: % acima do tipico", _pct(h.loc[cnes, "ac"], h.loc[cnes, "ld"]), pct_ac, 0.6)
        add("7", f"Hospital {cnes}: R$ por leito-dia", h.loc[cnes, "vp"] / h.loc[cnes, "ld"], rs_dia, 0.6)
    add("7", "Top 10: mil leitos-dia", top["ld"].sum() / 1e3, 711, 0.5)
    add("7", "Top 10: % do estado", _pct(top["ld"].sum(), ld), 38.7, 0.05)
    add("7", "Hospitais na safra", len(h), 260, 0)
    add("7", "Hospitais em dim_hospital com municipio", dim_hosp["nome_municipio"].notna().mean() * 100, 100, 0.5)

    # Pág. 8: municípios
    at = s.groupby("munic_atendimento")["leito_dias"].sum()
    for cod, esperado in [("520870", 44.7), ("520140", 7.2), ("520110", 6.8), ("522160", 4.9), ("521880", 4.4)]:
        add("8", f"Onde ficam os leitos: {nome_mun.get(cod, cod)} (%)", _pct(at.get(cod, 0), ld), esperado, 0.05)
    add("8", "Rosca: Goiania e o maior destino", at.idxmax() == "520870", 1, 0)
    rs_mun = s.groupby("munic_residencia").agg(ld=("leito_dias", "sum"), vp=("valor_pago", "sum"),
                                               n=("cid", "size"), fora=("fl_fora_municipio", "sum"))
    for cod, esperado in [("520870", 389_462), ("520140", 165_600), ("520110", 101_311)]:
        add("8", f"Leitos-dia dos moradores de {nome_mun.get(cod, cod)}", rs_mun.loc[cod, "ld"], esperado, 0)
    add("8", "Custo dos moradores de Aparecida de Goiania (R$ mi)", rs_mun.loc["520140", "vp"] / 1e6, 74.6, 0.05)
    dep = rs_mun[(rs_mun["n"] >= 3000) & rs_mun.index.str.startswith("52")]
    dep = (dep["fora"] / dep["n"] * 100).sort_values(ascending=False)
    for cod, esperado in [("521000", 67), ("520880", 66), ("522140", 64), ("522045", 61), ("521040", 54),
                          ("520450", 54), ("520025", 46), ("520140", 45)]:
        add("8", f"Dependencia: {nome_mun.get(cod, cod)} (% fora)", dep.get(cod, np.nan), esperado, 0.5)
    add("8", "Dependencia: 8 municipios com 3.000+ internacoes", len(dep.head(8)), 8, 0)

    # Pág. 9: permanência além do típico
    f = s.groupby("faixa_duracao").agg(n=("cid", "size"), ld=("leito_dias", "sum"))
    for faixa, p_n, p_ld in [("0 dia", 10.6, 0.0), ("1–3", 58.2, 26.5), ("4–7", 17.9, 22.8),
                             ("8–15", 8.9, 23.4), ("16–30", 3.7, 20.0), ("> 30", 0.7, 7.3)]:
        add("9", f"Faixa {faixa}: % internacoes", _pct(f.loc[faixa, "n"], n), p_n, 0.05)
        add("9", f"Faixa {faixa}: % leitos-dia", _pct(f.loc[faixa, "ld"], ld), p_ld, 0.05)
    add("9", "Dias acima do tipico (total)", acima, 806_293, 0)
    add("9", "% acima do tipico", _pct(acima, ld), 43.9, 0.05)
    for grupo, mil, pct in [("Lesões e traumas", 141.7, 49), ("Respiratório", 105.4, 46),
                            ("Circulatório", 101.4, 46), ("Digestivo", 66, 44), ("Infecciosas", 65, 42),
                            ("Geniturinário", 62, 47), ("Câncer", 42, 45), ("Gravidez e parto", 39, 27)]:
        add("9", f"{grupo}: mil dias acima", g.loc[grupo, "ac"] / 1e3, mil, 0.5)
        add("9", f"{grupo}: % dos seus dias", _pct(g.loc[grupo, "ac"], g.loc[grupo, "ld"]), pct, 0.5)
    for cnes, esperado in [("0965324", 56.5), ("2338424", 56.2), ("2338262", 55.9)]:
        add("9", f"Hospital {cnes}: % acima do tipico", _pct(h.loc[cnes, "ac"], h.loc[cnes, "ld"]), esperado, 0.05)
    add("9", "Hospital 2506815: permanencia media", h.loc["2506815", "ld"] / h.loc["2506815", "n"], 3.5, 0.05)
    add("9", "Hospital 2506815: % acima do tipico",
        _pct(h.loc["2506815", "ac"], h.loc["2506815", "ld"]), 35.9, 0.05)

    # Pág. 10 e 2: calendário de ocupação (dim_tempo[ano] = 2025)
    o = ocupacao[ocupacao["data"].dt.year == SAFRA_PADRAO]
    dia = o.groupby("data")[["pacientes_internados", "entradas", "altas"]].sum()
    semana = dia.groupby(dia.index.dayofweek).mean()
    for i, esperado in enumerate([1421, 1435, 1399, 1394, 1279, 936, 943]):
        add("10", f"Entradas por dia: {NOMES_DIA[i]}", semana.loc[i, "entradas"], esperado, 0.5, True)
    add("10", "Altas por dia: sex", semana.loc[4, "altas"], 1467, 0.5, True)
    add("10", "Altas por dia: dom", semana.loc[6, "altas"], 934, 0.5, True)
    mes = dia.groupby(dia.index.month)["pacientes_internados"].mean()
    add("10", "Mes mais cheio e maio", mes.idxmax() == 5, 1, 0, True)
    add("10", "Maio: internados por dia", mes.loc[5], 5250, 0.5, True)
    grp = o.groupby(["data", "grupo_doenca"])["pacientes_internados"].sum().reset_index()
    grp = grp.groupby([grp["grupo_doenca"], grp["data"].dt.month])["pacientes_internados"].mean()
    for grupo, rotulo, menor, maior in [("Lesões e traumas", "Traumas", 755, 817),
                                        ("Respiratório", "Respiratorio", 455, 818),
                                        ("Circulatório", "Circulatorio", 573, 661)]:
        add("10", f"{rotulo}: menor mes (internados/dia)", grp.loc[grupo].min(), menor, 0.5, True)
        add("10", f"{rotulo}: maior mes (internados/dia)", grp.loc[grupo].max(), maior, 0.5, True)
    resp = grp.loc["Respiratório"]
    add("2", "Respiratorio sobe em maio (% sobre a media do ano)", (resp.loc[5] / resp.mean() - 1) * 100, 31, 1, True)

    # Pág. 11: sazonalidade (lida da própria tabela sazonalidade_mensal)
    sz = sazonalidade.set_index(["grupo_doenca", "mes"])
    tot = ROTULO_TOTAL_SAZONALIDADE
    add("11", "Total: media do ano (internados/dia)", sz.loc[(tot, 1), "media_ano"], 5052.8, 0.05, True)
    add("11", "Total: pico em maio (internados/dia)", sz.loc[(tot, 5), "internados_dia"], 5250.4, 0.05, True)
    add("11", "Total: maio % sobre a media", sz.loc[(tot, 5), "variacao_pct"], 3.9, 0.05, True)
    add("11", "Total: dezembro (internados/dia)", sz.loc[(tot, 12), "internados_dia"], 4806.8, 0.05, True)
    add("11", "Total: dezembro % sobre a media", sz.loc[(tot, 12), "variacao_pct"], -4.9, 0.05, True)
    add("11", "Total: maio e o pico e dezembro o vale",
        sz.loc[(tot, 5), "fl_pico"] == 1 and sz.loc[(tot, 12), "fl_vale"] == 1, 1, 0, True)
    for grupo, mes_, esperado in [("Respiratório", 5, 30.9), ("Respiratório", 6, 27.7), ("Respiratório", 12, -27.2),
                                  ("Infecciosas", 4, 13.2), ("Infecciosas", 8, -14.5),
                                  ("Geniturinário", 11, 11.8), ("Câncer", 11, 8.7),
                                  ("Lesões e traumas", 1, -4.7), ("Lesões e traumas", 8, 3.1)]:
        add("11", f"{grupo} {NOMES_MES[mes_ - 1]}: % sobre a media", sz.loc[(grupo, mes_), "variacao_pct"],
            esperado, 0.05, True)
    add("11", "Grupos no mapa (10 maiores + total)", sazonalidade["grupo_doenca"].nunique() >= 11, 1, 0, True)

    # P29: tendência (lida da própria tabela tendencia_anual)
    td = tendencia.set_index("ano")["internados_dia"]
    for ano, esperado in [(2022, 4397.9), (2023, 4734.1), (2024, 4854.3), (2025, 5052.8)]:
        add("P29", f"Tendencia {ano}: internados por dia", td.get(ano, np.nan), esperado, 0.05, True)
    add("P29", "Tendencia 2025 = media do ano do Total da rede (sazonalidade)",
        td.get(SAFRA_PADRAO, np.nan), sz.loc[(tot, 1), "media_ano"], 0.05, True)
    add("P29", "A rede cresce todo ano (2022 a 2025)", bool(td.is_monotonic_increasing), 1, 0, True)
    return r


def conferir_numeros_pdf(numeros: list[tuple], ocupacao_completa: bool) -> None:
    print(f"\nConferencia com o PDF (safra {SAFRA_PADRAO}): {len(numeros)} numeros")
    divergentes, pulados, pagina = [], 0, None
    for pag, desc, valor, esperado, tol, ocup in numeros:
        if pag != pagina:
            print(f"  pagina {pag} do PDF")
            pagina = pag
        if ocup and not ocupacao_completa:
            pulados += 1
            print(f"  ..   {desc}: {valor:,.1f} (esperado {esperado:,.1f}) PULADO")
            continue
        ok = abs(valor - esperado) <= tol + 1e-9
        print(f"  {'OK' if ok else 'XX'}   {desc}: {valor:,.1f} (esperado {esperado:,.1f})")
        if not ok:
            divergentes.append(f"pag. {pag} - {desc}: {valor:,.2f} (esperado {esperado:,.2f})")
    if pulados:
        print(f"\nAviso: {pulados} numeros da ocupacao diaria nao foram conferidos porque a base nao tem as "
              f"competencias de {SAFRA_PADRAO - 1} e {SAFRA_PADRAO + 1} (quem entra em dez/{SAFRA_PADRAO} "
              f"so e cobrado em {SAFRA_PADRAO + 1}).")
    if divergentes:
        raise SystemExit("\nERRO: numeros diferentes do PDF:\n  - " + "\n  - ".join(divergentes))
    print(f"  Todos os {len(numeros) - pulados} numeros conferidos batem com o PDF.")


# Execução

def main() -> None:
    print(f"Gerando as tabelas do GiroSUS em: {PASTA_SAIDA}")
    print("Carregando SIH (AIH regular)...")
    df = carregar_sih()
    raw = carregar_complementos_raw()

    print("Montando fato_internacoes...")
    todas_safras = montar_fato_internacoes(df, raw)
    safras = set(todas_safras["safra"].unique())
    # Tudo olha só para a safra 2025, como o PDF.
    fato = todas_safras[todas_safras["safra"] == SAFRA_PADRAO].reset_index(drop=True)

    print("Montando fato_ocupacao_diaria (pode levar alguns minutos)...")
    # Quem estava internado em 2025 inclui AIHs cobradas em 2024 e 2026; fica só com os dias de 2025.
    grupos = {cid: classificar_grupo(cid) for cid in todas_safras["cid"].unique()}
    ocupacao = montar_fato_ocupacao(todas_safras, grupos)
    ocupacao = ocupacao[ocupacao["data"].dt.year == SAFRA_PADRAO].reset_index(drop=True)

    municipios = nomes_municipios()
    dim_diagnostico = montar_dim_diagnostico(fato)
    dim_municipio = montar_dim_municipio(fato, municipios)
    # Hospitais da safra 2025 e também os que só aparecem na ocupação de 2025.
    cnes_2025 = set(fato["cnes"]) | set(ocupacao["cnes"])
    dim_hospital = montar_dim_hospital(todas_safras[todas_safras["cnes"].isin(cnes_2025)], municipios)
    dim_procedimento = montar_dim_procedimento(fato)
    sazonalidade = montar_sazonalidade(ocupacao)
    tendencia = montar_tendencia(todas_safras)

    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    for antigo in PASTA_SAIDA.glob("*.parquet"):  # versões antigas: a saída agora é só CSV
        try:
            antigo.unlink()
        except PermissionError:
            raise SystemExit(f"\nERRO: nao consegui apagar {antigo.name}. Feche o Power BI e rode de novo.")
    tabelas = {
        "fato_internacoes": fato,
        "fato_ocupacao_diaria": ocupacao,
        "dim_tempo": montar_dim_tempo(fato),
        "dim_diagnostico": dim_diagnostico,
        "dim_procedimento": dim_procedimento,
        "dim_hospital": dim_hospital,
        "dim_municipio_residencia": dim_municipio,
        "dim_municipio_atendimento": dim_municipio,
        "sazonalidade_mensal": sazonalidade,
        "tendencia_anual": tendencia,
    }
    for nome_tabela, tabela in tabelas.items():
        gravar(tabela, PASTA_SAIDA / f"{nome_tabela}.csv")
        gravar_power_query(nome_tabela, tabela)
        print(f"Gerado: {nome_tabela} ({len(tabela):,} linhas)")

    conferir_saida()
    numeros = calcular_numeros_pdf(fato, ocupacao, dim_diagnostico, dim_hospital, dim_municipio, sazonalidade,
                                   tendencia)
    conferir_numeros_pdf(numeros, ocupacao_completa={SAFRA_PADRAO - 1, SAFRA_PADRAO + 1} <= safras)
    print(f"\nPronto. As 10 tabelas do Power BI estao em: {PASTA_SAIDA}")
    print(f"Consultas prontas para o Power BI (codigos como Texto, decimal ','): {PASTA_POWER_QUERY}")


if __name__ == "__main__":
    main()

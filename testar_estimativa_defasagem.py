# -*- coding: utf-8 -*-
"""
GiroSUS: teste da estimativa dos meses incompletos (defasagem do SIH).

Por que existe:
    O SIH chega com atraso: o hospital apresenta a conta (AIH) no mês da alta ou
    nos meses seguintes. Por isso o mês mais recente sempre chega incompleto.
    Este script mede esse atraso e testa, com os dados de 2025, se dá para completar
    os meses recentes com uma estimativa. Os números do slide "Como lidamos com a
    defasagem" saem daqui.

Como usar (na pasta do projeto, com o .venv ativo):
    python testar_estimativa_defasagem.py

O que ele faz:
    1. Atraso da cobrança: das altas de 2024, quanto foi cobrado no mesmo mês da alta,
       até 1, 2 e 3 meses depois.
    2. Estimativa de internações: para cada mês de 2025 ("voltando no tempo"), olha só o
       que já tinha chegado e completa o resto com a curva de atraso dos 12 meses de altas
       já fechadas (de 18 a 7 meses antes). Compara com o que chegou depois.
    3. Estimativa de custo: custo estimado do mês = leitos-dia estimados × R$ por leito-dia
       dos últimos 3 meses fechados, por grupo de doença. Compara com o valor real.
    No fim, confere os números com os do slide e para com ERRO se algum mudar.

Regras de negócio: as mesmas de gerar_modelo_bi_girosus.py (só AIH nova, IDENT = 1).
O mês é o mês da alta (data de saída); a cobrança é a competência (ANO_CMPT/MES_CMPT).
"""

import numpy as np
import pandas as pd

import gerar_modelo_bi_girosus as g

ANO_TESTE = 2025
ANO_CURVA = ANO_TESTE - 1


def carregar() -> pd.DataFrame:
    f = g.montar_fato_internacoes(g.carregar_sih(), None)  # UTI e acompanhante não entram no teste
    f["grupo"] = f["cid"].map(g.classificar_grupo)
    f["mes_alta"] = f["data_saida"].dt.to_period("M")
    f["mes_cobranca"] = f["competencia"].dt.to_period("M")
    f["atraso"] = (f["mes_cobranca"] - f["mes_alta"]).apply(lambda x: x.n)
    return f


def atraso_da_cobranca(f: pd.DataFrame) -> pd.Series:
    altas = f[f["mes_alta"].dt.year == ANO_CURVA]
    dist = altas["atraso"].clip(lower=0).value_counts(normalize=True).sort_index()
    return (dist.cumsum() * 100).round(1)


def estimar_internacoes(f: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for corte in pd.period_range(f"{ANO_TESTE}-01", f"{ANO_TESTE}-12", freq="M"):
        fechadas = f[(f["mes_alta"] >= corte - 18) & (f["mes_alta"] <= corte - 7)]
        for k in range(0, 3):
            mes = corte - k
            completude = (fechadas["atraso"] <= k).mean()
            chegou = ((f["mes_alta"] == mes) & (f["mes_cobranca"] <= corte)).sum()
            real = (f["mes_alta"] == mes).sum()
            linhas.append((str(corte), k, chegou, chegou / completude, real))
    r = pd.DataFrame(linhas, columns=["corte", "meses_antes", "so_o_que_chegou", "estimado", "real"])
    r["erro_so_chegou_pct"] = (r["so_o_que_chegou"] / r["real"] - 1).abs() * 100
    r["erro_estimado_pct"] = (r["estimado"] / r["real"] - 1).abs() * 100
    return r


def estimar_custo(f: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for corte in pd.period_range(f"{ANO_TESTE}-01", f"{ANO_TESTE}-12", freq="M"):
        base = f[(f["mes_alta"] >= corte - 18) & (f["mes_alta"] <= corte - 7)]
        atraso = base["atraso"].clip(lower=0)
        for k in (0, 1):
            mes = corte - k
            completude = ((base["leito_dias"] * (atraso <= k)).groupby(base["grupo"]).sum()
                          / base.groupby("grupo")["leito_dias"].sum())
            chegou = (f[(f["mes_alta"] == mes) & (f["mes_cobranca"] <= corte)]
                      .groupby("grupo").agg(ld=("leito_dias", "sum"), vp=("valor_pago", "sum")))
            ld_estimado = chegou["ld"] / completude.reindex(chegou.index).fillna(1)
            # R$ por leito-dia dos últimos 3 meses fechados (altas de 5 a 3 meses antes do corte)
            fechados = (f[(f["mes_alta"] >= corte - 5) & (f["mes_alta"] <= corte - 3) & (f["mes_cobranca"] <= corte)]
                        .groupby("grupo").agg(ld=("leito_dias", "sum"), vp=("valor_pago", "sum")))
            rs = (fechados["vp"] / fechados["ld"]).reindex(chegou.index)
            estimado = (ld_estimado * rs).sum()
            real = f.loc[f["mes_alta"] == mes, "valor_pago"].sum()
            linhas.append((str(corte), k, chegou["vp"].sum(), estimado, real))
    r = pd.DataFrame(linhas, columns=["corte", "meses_antes", "so_o_que_chegou", "estimado", "real"])
    r["erro_so_chegou_pct"] = (r["so_o_que_chegou"] / r["real"] - 1).abs() * 100
    r["erro_estimado_pct"] = (r["estimado"] / r["real"] - 1).abs() * 100
    return r


def main() -> None:
    print("Carregando SIH (AIH regular)...")
    f = carregar()

    acum = atraso_da_cobranca(f)
    print(f"\n1. Atraso da cobrança (altas de {ANO_CURVA}, % já cobrado):")
    for k in range(4):
        print(f"   até {k} mês(es) depois da alta: {acum.get(k, 100):.1f}%")

    ri = estimar_internacoes(f)
    print(f"\n2. Estimativa de internações (12 meses de {ANO_TESTE}), erro médio:")
    ei = ri.groupby("meses_antes")[["erro_so_chegou_pct", "erro_estimado_pct"]].mean().round(1)
    for k, row in ei.iterrows():
        rotulo = "mês mais recente" if k == 0 else f"{k} mês(es) antes"
        print(f"   {rotulo}: só o que chegou {row.iloc[0]:.1f}% · estimativa {row.iloc[1]:.1f}%")

    rc = estimar_custo(f)
    print(f"\n3. Estimativa de custo (12 meses de {ANO_TESTE}), erro médio:")
    ec = rc.groupby("meses_antes")[["erro_so_chegou_pct", "erro_estimado_pct"]].mean().round(1)
    for k, row in ec.iterrows():
        rotulo = "mês mais recente" if k == 0 else f"{k} mês(es) antes"
        print(f"   {rotulo}: só o que chegou {row.iloc[0]:.1f}% · estimativa {row.iloc[1]:.1f}%")

    # Conferência com os números do slide e do README
    esperado = [
        ("cobrado no mesmo mês da alta", acum.get(0), 65.1),
        ("cobrado em até 3 meses", acum.get(3), 99.4),
        ("internações, mês mais recente, só o que chegou", ei.loc[0].iloc[0], 29.4),
        ("internações, mês mais recente, estimativa", ei.loc[0].iloc[1], 8.4),
        ("internações, 1 mês antes, só o que chegou", ei.loc[1].iloc[0], 12.5),
        ("internações, 1 mês antes, estimativa", ei.loc[1].iloc[1], 2.7),
        ("custo, mês mais recente, só o que chegou", ec.loc[0].iloc[0], 32.2),
        ("custo, mês mais recente, estimativa", ec.loc[0].iloc[1], 4.8),
        ("custo, 1 mês antes, estimativa", ec.loc[1].iloc[1], 4.0),
    ]
    divergentes = [f"{d}: {v:.1f} (esperado {e:.1f})" for d, v, e in esperado if abs(v - e) > 0.05]
    if divergentes:
        raise SystemExit("\nERRO: números diferentes do slide:\n  - " + "\n  - ".join(divergentes))
    print(f"\nOK: os {len(esperado)} números do slide \"Como lidamos com a defasagem\" batem.")


if __name__ == "__main__":
    main()

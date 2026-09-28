"""
Converte os arquivos .dbc do DATASUS (SIH e CNES) para .parquet.

Como usar (na pasta do projeto, com o .venv ativo):
    1. Baixe os arquivos do mês no site do DATASUS (Transferência de Arquivos):
       RDGOAAMM.dbc (SIH) e LTGOAAMM.dbc (CNES), AA = ano com 2 dígitos, MM = mês.
    2. Coloque cada um na pasta do ano: data/raw/sih/<ano>/ ou data/raw/cnes/<ano>/.
    3. Rode:
           python -m src.converter_dbc

O script procura, nos anos de src/config.py, todo .dbc que ainda não tem o
.parquet com o mesmo nome ao lado e converte (todas as colunas como texto,
igual aos arquivos que já estão no repositório). Os que já têm .parquet são
pulados. Usa o PySUS, que já está no requirements.txt.
"""

import asyncio
from pathlib import Path

from pysus.api.extensions import ExtensionFactory

from src.config import ANOS, CNES_RAW_DIR, SIH_RAW_DIR

PADROES = [(SIH_RAW_DIR, "RDGO*.dbc"), (CNES_RAW_DIR, "LTGO*.dbc")]


# Lista os .dbc que ainda não foram convertidos

def listar_pendentes() -> list[Path]:
    pendentes = []
    for pasta, padrao in PADROES:
        for ano in ANOS:
            for dbc in sorted((pasta / str(ano)).glob(padrao)):
                if not dbc.with_suffix(".parquet").exists():
                    pendentes.append(dbc)
    return pendentes


# Converte um .dbc em .parquet ao lado dele

async def converter(dbc: Path) -> None:
    arquivo = await ExtensionFactory.instantiate(dbc)
    await arquivo.to_parquet(output_path=dbc.with_suffix(".parquet"))


def converter_dbc() -> None:
    pendentes = listar_pendentes()
    if not pendentes:
        print("Nada a converter: todo .dbc já tem o .parquet ao lado.")
        return

    print(f"Convertendo {len(pendentes)} arquivo(s)...")
    for dbc in pendentes:
        asyncio.run(converter(dbc))
        print(f"  OK  {dbc.parent.parent.name}/{dbc.parent.name}/{dbc.with_suffix('.parquet').name}")

    print("\nPronto. Próximo passo: python -m src.pipeline")


if __name__ == "__main__":
    converter_dbc()

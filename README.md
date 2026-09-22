# leitos-sus

Análise da demanda hospitalar em Goiás usando dados públicos do SUS (SIH e CNES) e do IBGE, com foco em entender onde e como as internações pressionam a rede de saúde.

## Sumário

* [Como rodar o projeto](#como-rodar-o-projeto)
* [Estrutura do projeto](#estrutura-do-projeto)
* [Como funciona o negócio](#como-funciona-o-negócio)
* [Como funcionam os notebooks](#como-funcionam-os-notebooks)
* [Como funcionam os testes](#como-funcionam-os-testes)
* [Como funciona o pipeline](#como-funciona-o-pipeline)
* [Perguntas frequentes](#perguntas-frequentes)
* [Referências e benchmarks](#referências-e-benchmarks)
* [Datasets utilizados](#datasets-utilizados)
* [O que ainda falta](#o-que-ainda-falta)

## Como rodar o projeto

Requisito: Python 3.12.

```bash
# Criar o ambiente virtual
python3.12 -m venv .venv

# Ativar o ambiente virtual
# Linux/macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate

# Instalar as dependências
pip install -r requirements.txt
```

## Estrutura do projeto

```
leitos-sus/
├── 📊 dashboard/         # Dashboard / visualização final (em construção)
├── 🗂️ data/
│   ├── raw/               # Dados brutos baixados (SIH, CNES, IBGE)
│   └── silver/            # Dados já tratados e validados
├── 📓 notebooks/         # Jupyter notebooks de exploração e análise
├── 🐍 src/
│   ├── config.py           # Caminhos e parâmetros do projeto
│   ├── pipeline.py          # Execução local do pipeline (ETL)
│   ├── extract/            # Extração dos dados por fonte (SIH, CNES, IBGE)
│   ├── transform/           # Tratamento e padronização dos dados
│   └── orchestration/      # Orquestração do pipeline com Prefect
├── ✅ tests/             # Testes automatizados (pytest)
├── requirements.txt       # Dependências do projeto
└── README.md
```

## Como funciona o negócio

<details>
<summary>🏥 O que é uma AIH e por que isso importa</summary>

AIH é a Autorização de Internação Hospitalar, o documento que registra cada internação no SUS. O projeto usa apenas AIHs regulares (campo IDENT igual a 1). AIHs de longa permanência (IDENT igual a 5) são descartadas da contagem de novas internações, porque representam continuidade de um mesmo tratamento e inflariam os números.
</details>

<details>
<summary>📅 Por que o recorte vai só até junho de 2026</summary>

O projeto cobre janeiro de 2021 a junho de 2026. O ano de 2026 ainda está em andamento na base de dados, então ele entra apenas parcial. Comparações de sazonalidade e volume usam somente anos completos (2021 a 2025) para não distorcer o resultado.
</details>

<details>
<summary>📍 Recorte geográfico</summary>

O projeto olha para o estado de Goiás (UF GO, código IBGE 52). As internações consideradas nos indicadores por população são apenas de pacientes residentes em municípios goianos.
</details>

<details>
<summary>🗓️ Por que existem várias bases de população com safras diferentes</summary>

Dentro de `data/raw/ibge` não existe uma única fonte de população cobrindo todos os anos, cada ano vem de uma publicação diferente do IBGE, então o projeto combina várias safras:

* 2021: estimativa populacional anual publicada pelo IBGE (`estimativas/2021`).
* 2022: população do Censo 2022, na versão republicada pelo IBGE para o TCU (`tcu_2023`), não a estimativa anual.
* 2023: não existe fonte oficial do IBGE para esse ano. O valor usado é calculado pelo próprio projeto, pela média entre a população de 2022 e a de 2024 (interpolação), e fica marcado na base com origem "Cálculo próprio com dados IBGE".
* 2024, 2025 e 2026: estimativas populacionais anuais publicadas pelo IBGE (`estimativas/2024`, `estimativas/2025`, `estimativas/2026`).

Nem tudo que está em `data/raw/ibge` é usado pelo pipeline. Os microdados do Censo 2022 em `censo_2022/` (domicílios, famílias, mortalidade) e o arquivo de população por UF em `tcu_2023/POP_TCU_2023_Brasil_e_UFs...` foram baixados como referência, mas não entram na base final, só a planilha de população por município do TCU é usada.

O CNES e o SIH não têm esse problema, ali é a mesma fonte mês a mês, todos os arquivos mensais de `data/raw/cnes` e `data/raw/sih` no período do projeto são lidos e usados.
</details>

<details>
<summary>🫁 Como uma doença respiratória é identificada</summary>

Uma internação é classificada como respiratória quando o diagnóstico principal (coluna DIAG_PRINC) começa com a letra J, que corresponde ao Capítulo X da CID 10, doenças do aparelho respiratório (J00 a J99).
</details>

<details>
<summary>📈 O que as análises já responderam</summary>

Internações respiratórias representam cerca de 9% do total de internações em Goiás, com pico entre abril e junho. Municípios menores têm taxa de internação por habitante mais alta que municípios grandes, mesmo tendo menos casos em número absoluto. Comparadas às demais internações, elas têm mortalidade mais que o dobro, tempo de internação maior e uso de UTI quase duas vezes mais frequente.
</details>

## Como funcionam os notebooks

<details>
<summary>📓 Um notebook por etapa da análise</summary>

Os notebooks seguem uma ordem numerada, e cada um tem uma responsabilidade específica:

* `01`, `02`, `03`: exploração de cada fonte isolada (SIH, CNES, IBGE), entendendo dimensão, tipos, nulos e duplicidades.
* `04`: consolidação das bases em um único dataset multianual por fonte.
* `05`: análise integrada, cruzando as três fontes para responder a pergunta de negócio principal.
* `06`: recorte temático, aprofundando em um assunto específico (doenças respiratórias).
</details>

<details>
<summary>🔁 Por que os notebooks usam os dados de data/silver</summary>

Os notebooks de análise (04 em diante) leem sempre os arquivos Parquet já tratados em `data/silver`, nunca os dados brutos diretamente. Isso garante que todo mundo do grupo está analisando a mesma versão validada dos dados, gerada pelo pipeline.
</details>

## Como funcionam os testes

<details>
<summary>✅ O que os testes garantem</summary>

Os testes ficam em `tests/` e rodam com pytest. Eles verificam:

* Colunas críticas sem valores nulos (por exemplo, data de internação, código do município, CNES).
* Ausência de duplicidade em chaves (por exemplo, código do município mais ano na base de população).
* Cobertura temporal completa, conferindo se todos os meses do período esperado estão presentes.
* Formato válido dos códigos de município (7 dígitos no IBGE, 6 dígitos no SIH).
* Igualdade entre o dado gerado em staging e o dado final validado em silver.
</details>

<details>
<summary>▶️ Como rodar os testes</summary>

```bash
pytest
```
</details>

## Como funciona o pipeline

<details>
<summary>⚙️ As três etapas por fonte de dado</summary>

Cada fonte (SIH, CNES, IBGE) passa por três etapas, cada uma em sua própria pasta dentro de `src/`:

1. `extract/`: lê os arquivos brutos e carrega em DataFrame, sem transformar nada.
2. `transform/`: limpa, padroniza tipos e corrige inconsistências.
3. O resultado é salvo em Parquet, primeiro em staging, depois validado e promovido para `data/silver`.
</details>

<details>
<summary>▶️ Como rodar o pipeline inteiro</summary>

De forma simples, com um script sequencial:

```bash
python -m src.pipeline
```

Ou orquestrado com Prefect, que também é responsável por rodar tudo com um único comando:

```bash
python -m src.orchestration.prefect_flow
```
</details>

<details>
<summary>📦 Por que Parquet em vez de CSV</summary>

Parquet é um formato colunar, mais compacto e mais rápido de ler que CSV, e mantém o tipo de cada coluna salvo junto com o arquivo. Isso evita ter que reconverter tipos toda vez que alguém abre os dados tratados.
</details>

## Perguntas frequentes

<details>
<summary>🐍 Qual linguagem e quais bibliotecas o projeto usa</summary>

Python, com pandas para manipulação de dados, pyarrow para ler e escrever Parquet, openpyxl e xlrd para ler planilhas do IBGE, prefect para orquestração do pipeline e pytest para os testes.
</details>

<details>
<summary>🗂️ Existe um dicionário de dados</summary>

Ainda não. Esse é um ponto pendente do projeto: falta uma tabela reunindo nome da coluna, tipo, significado e fonte de cada variável usada.
</details>

<details>
<summary>🔄 O pipeline é repetível do zero</summary>

Sim. A extração e a transformação são scriptadas, não manuais, então qualquer pessoa do grupo pode rodar `python -m src.pipeline` (ou o flow do Prefect) e reproduzir os dados tratados do início.
</details>

<details>
<summary>🚧 O que ainda não existe neste projeto</summary>

A idade e o sexo do paciente ainda não são extraídos do SIH, então hoje não é possível segmentar a análise respiratória por faixa etária, por exemplo crianças ou idosos.
</details>

## Referências e benchmarks

* **SUS 360º**
  Estrutura por módulos, KPIs, leitos, capacidade e mapas.
  [Acessar SUS 360º](https://sus360.saude.gov.br/)

* **ElastiCNES**
  Referência para mapas, tipos de leitos e filtros geográficos.
  [Acessar ElastiCNES](https://elasticnes.saude.gov.br/)

* **Internações Hospitalares, São Paulo**
  Referência para dimensões, filtros e perguntas possíveis utilizando dados de internações hospitalares.
  [Acessar Internações Hospitalares](https://prefeitura.sp.gov.br/web/saude/tabnet/internacoes_hospitalares)

* **Painel e-SUS APS**
  Referência de experiência do usuário (UX) e organização de informações para gestão em saúde.
  [Acessar e-SUS APS](https://sisaps.saude.gov.br/sistemas/esusaps/)

* **Observatório de Saúde Infantil**
  Projeto no GitHub que utiliza dados do SIM e SIH para análise de mortalidade e internações de crianças de 0 a 6 anos.
  [Acessar repositório](https://github.com/fmdsocial/sim-sih-mortalidade-internacoes-0-6-anos)

* **SUS Data Analysis**
  Repositório com análises utilizando dados públicos do SUS.
  [Acessar repositório](https://github.com/claudioavgo/sus-data-analysis)

## Datasets utilizados

<details>
<summary>🏥 SIH/SUS, Internações Hospitalares (AIH)</summary>

**O que é:** base de dados de internações hospitalares do SUS contendo informações como procedimentos, diagnósticos, datas de internação e saída, município de residência, município de atendimento e valores registrados nas AIHs.

**Fonte:** [DATASUS, Transferência de Arquivos](https://datasus.saude.gov.br/transferencia-de-arquivos/)

**Base utilizada:** SIH/SUS, arquivos de AIH Reduzida (RD).
</details>

<details>
<summary>🛏️ CNES, Estabelecimentos e Leitos</summary>

**O que é:** Cadastro Nacional de Estabelecimentos de Saúde, utilizado para obter informações sobre estabelecimentos, tipos de leitos e capacidade hospitalar instalada.

**Fonte:** [DATASUS, Transferência de Arquivos](https://datasus.saude.gov.br/transferencia-de-arquivos/)

**Base utilizada:** CNES, arquivos de Leitos (LT).
</details>

<details>
<summary>👥 IBGE, População Municipal</summary>

**Uso no projeto:** os dados populacionais são utilizados como referência para contextualização e normalização de indicadores, como internações por 10 mil habitantes.

**Estimativas da População:** estimativas anuais da população dos municípios brasileiros.
[Acessar Estimativas da População](https://ftp.ibge.gov.br/Estimativas_de_Populacao/)

**Censo Demográfico 2022, População e Domicílios:** resultados do Censo Demográfico 2022 relacionados à população e aos domicílios.
[Acessar Censo Demográfico 2022](https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Populacao_e_domicilios_Primeiros_resultados/)

**População dos Municípios enviada ao TCU, 2023:** arquivos publicados pelo IBGE para divulgação da população dos municípios ao Tribunal de Contas da União (TCU).
[Acessar arquivos do TCU](https://ftp.ibge.gov.br/Informacoes_Gerais_e_Referencia/Relacao_da_Populacao_dos_Municipios_para_publicacao_no_DOU_em_2023/)
</details>

## O que ainda falta

* 📊 Modelagem dos dados para Power BI (modelo estrela, medidas em DAX).
* 🖥️ Construção do dashboard (pasta `dashboard/` ainda vazia).
* 📖 Dicionário de dados com nome, tipo, significado e fonte de cada coluna usada.

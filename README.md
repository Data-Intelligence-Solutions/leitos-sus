# leitos-sus

Análise da demanda hospitalar em Goiás usando dados públicos do SUS (SIH e CNES) e do IBGE, com foco em entender onde e como as internações pressionam a rede de saúde.

## Sumário

* [Como rodar o projeto](#como-rodar-o-projeto)
* [Estrutura do projeto](#estrutura-do-projeto)
* [Fluxo dos dados](#fluxo-dos-dados)
* [Como funciona o negócio](#como-funciona-o-negócio)
* [Como funcionam os notebooks](#como-funcionam-os-notebooks)
* [Como funcionam os testes](#como-funcionam-os-testes)
* [Como funciona o pipeline](#como-funciona-o-pipeline)
* [Como atualizar os dados](#como-atualizar-os-dados)
* [Solução de problemas](#solução-de-problemas)
* [Como contribuir](#como-contribuir)
* [Perguntas frequentes](#perguntas-frequentes)
* [Referências e benchmarks](#referências-e-benchmarks)
* [Datasets utilizados](#datasets-utilizados)
* [O que ainda falta](#o-que-ainda-falta)

## Como rodar o projeto

Requisito: Python 3.12.

Todos os comandos abaixo são para o terminal **Git Bash** (Windows):

```bash
# Criar o ambiente virtual
py -3.12 -m venv .venv

# Ativar o ambiente virtual
source .venv/Scripts/activate

# Conferir a versão do Python (deve mostrar 3.12.x)
python --version

# Instalar as dependências
pip install -r requirements.txt

# Desativar o ambiente virtual quando terminar
deactivate
```

> Se o comando `py` não for reconhecido, use `python -m venv .venv` (desde que `python --version` mostre 3.12).

## Estrutura do projeto

```
leitos-sus/
├── 📊 dashboard/         # Dashboard / visualização final (em construção)
├── 🗂️ data/
│   ├── raw/               # Dados de origem: SIH e CNES em Parquet (convertidos do DBC), IBGE em planilhas
│   ├── staging/           # Saída do pipeline (gerada localmente, não vai para o Git)
│   └── silver/            # Bases consolidadas e validadas, usadas nas análises
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

## Fluxo dos dados

```
DATASUS (.dbc)  ──conversão──▶  data/raw/sih, data/raw/cnes (.parquet)
IBGE (.xls/.xlsx) ───────────▶  data/raw/ibge
                                     │
                                     ▼
                         src/pipeline.py (ETL)
                                     │
                                     ▼
                         data/staging/*.parquet
                                     │  pytest valida
                                     ▼
                         data/silver/*.parquet  (cópia validada, feita à mão)
                                     │
                                     ▼
                      notebooks 05 e 06 (análises)
```

<details>
<summary>🔎 Quem faz cada etapa</summary>

| Etapa | Onde acontece | Resultado |
|---|---|---|
| Download dos arquivos mensais do SIH (RD) e do CNES (LT) | Manual, no site do DATASUS | Arquivos `.dbc` |
| Conversão de `.dbc` para `.parquet` | Feita fora do pipeline (os `.dbc` são lidos com o PySUS). O script dessa conversão ainda não está no repositório | `data/raw/sih/<ano>/RDGO*.parquet` e `data/raw/cnes/<ano>/LTGO*.parquet` |
| Download das planilhas de população | Manual, no FTP do IBGE | `data/raw/ibge/...` |
| Extração e transformação | `src/pipeline.py` ou o flow do Prefect | `data/staging/*.parquet` |
| Validação | `pytest` | Confere a qualidade da staging e se ela é igual à silver |
| Promoção para silver | Manual: copiar os arquivos validados de `data/staging` para `data/silver`. Ainda não existe script para isso | `data/silver/*.parquet` |
| Análises | Notebooks `05` e `06` | Leem apenas `data/silver` |
</details>

<details>
<summary>⚠️ O notebook 04 e a pasta data/silver</summary>

O notebook `04` fez a primeira consolidação multianual e também grava em `data/silver`. Mas a silver atual é igual à saída do pipeline, e as duas não batem numa coluna: o `04` grava a data de internação do SIH (DT_INTER) como texto, enquanto o pipeline e a silver atual têm essa coluna como data.

Por isso, não rode a célula final do `04` (a que grava em `data/silver`) sem necessidade: ela sobrescreve a silver e faz o teste `test_sih_staging_igual_silver` falhar.
</details>

<details>
<summary>📁 Arquivos que não vêm no repositório</summary>

Alguns arquivos estão no `.gitignore` e não aparecem num `git clone`:

* `*.dbc`: arquivos originais do DATASUS. O repositório já traz a versão convertida em `.parquet`, que é o que o pipeline usa.
* `data/raw/ibge/censo_2022/Pessoas_52_publico.csv`: microdados do Censo, grandes demais para o Git e não usados na base final.
* `data/staging/`: gerada ao rodar o pipeline.
* `docs/`: documentação de referência local.
* `.venv/`: ambiente virtual de cada pessoa.
</details>

## Como funciona o negócio

<details>
<summary>🏥 O que é uma AIH e por que isso importa</summary>

AIH é a Autorização de Internação Hospitalar, o documento que registra cada internação no SUS. Na contagem de novas internações, o projeto descarta as AIHs de longa permanência (campo IDENT igual a 5), porque elas representam a continuidade de um mesmo tratamento e inflariam os números. Na prática, sobram as AIHs regulares (IDENT igual a 1).
</details>

<details>
<summary>📅 Por que o recorte vai só até junho de 2026</summary>

O projeto cobre janeiro de 2021 a junho de 2026. O ano de 2026 ainda está em andamento na base de dados, então ele entra apenas parcial. Comparações de sazonalidade e volume usam somente anos completos (2021 a 2025) para não distorcer o resultado.

As bases não terminam no mesmo mês: o SIH vai até junho de 2026 e o CNES até julho de 2026. As análises cortam as internações pela data de internação, entre 01/01/2021 e 30/06/2026.
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
<summary>📌 Onde essas regras são aplicadas</summary>

As regras de negócio acima não ficam no pipeline. O `src/` apenas extrai e padroniza os dados, mantendo todas as AIHs. Os filtros são aplicados nos notebooks de análise:

* Exclusão das AIHs de longa permanência (IDENT igual a 5) e corte do período pela data de internação: notebooks `05` e `06`.
* Recorte de pacientes residentes em Goiás: notebooks `05` e `06`, cruzando o município de residência (MUNIC_RES) com os códigos de município da base de população.
* Classificação de doença respiratória (CID J): notebook `06`.

Quem for criar um indicador novo deve reaplicar os mesmos filtros para os números baterem com as análises existentes.
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
* `04`: consolidação das bases em um único dataset multianual por fonte. Foi a primeira versão da consolidação que hoje o pipeline faz (veja [O notebook 04 e a pasta data/silver](#fluxo-dos-dados)).
* `05`: análise integrada, cruzando as três fontes para responder a pergunta de negócio principal.
* `06`: recorte temático, aprofundando em um assunto específico (doenças respiratórias).
</details>

<details>
<summary>🔁 Por que os notebooks de análise usam os dados de data/silver</summary>

Os notebooks de análise (`05` e `06`) leem sempre os arquivos Parquet já consolidados em `data/silver`, nunca os dados brutos diretamente. Isso garante que todo mundo do grupo está analisando a mesma versão validada dos dados, que é conferida pelos testes contra a saída do pipeline.
</details>

<details>
<summary>⚠️ Notebooks que dependem dos arquivos .dbc</summary>

Os notebooks `01`, `02` e `04` foram escritos para ler os arquivos `.dbc` originais com o PySUS. Como os `.dbc` não vêm no repositório, esses notebooks não rodam num clone novo: eles não encontram os arquivos e param com erro. Os notebooks `03`, `05` e `06` rodam normalmente.

Para rodar `01`, `02` e `04` hoje é preciso ter os `.dbc` nas pastas `data/raw/sih/<ano>` e `data/raw/cnes/<ano>`. A alternativa, ainda pendente, é adaptar esses notebooks para ler os `.parquet` que já estão no repositório.
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

Os testes leem os arquivos de `data/staging`, que não vêm no repositório. Num clone novo, rode o pipeline antes:

```bash
python -m src.pipeline
pytest
```

Sem esse primeiro passo, os testes falham com erro de arquivo não encontrado.
</details>

## Como funciona o pipeline

<details>
<summary>⚙️ As três etapas por fonte de dado</summary>

Cada fonte (SIH, CNES, IBGE) passa por três etapas, cada uma em sua própria pasta dentro de `src/`:

1. `extract/`: lê os arquivos de `data/raw` e carrega em DataFrame, sem transformar nada. No SIH e no CNES, lê os `.parquet` mensais do período definido em `src/config.py` e guarda o nome do arquivo de origem. No IBGE, lê as planilhas de população de cada ano.
2. `transform/`: padroniza os dados de cada fonte.
3. O resultado é salvo em Parquet em `data/staging`.

O pipeline não grava em `data/silver`. Depois de validada pelos testes, a staging é copiada à mão para `data/silver`. Os testes conferem se as duas são iguais.
</details>

<details>
<summary>🧹 O que cada transformação faz</summary>

* **SIH** (`transform/sih.py`): converte a data de internação (DT_INTER) para data. As demais colunas ficam como vieram.
* **CNES** (`transform/cnes.py`): extrai o ano e o mês da competência a partir do nome do arquivo (por exemplo, `LTGO2401` vira 2024, mês 1) e converte as quantidades de leitos (QT_EXIST, QT_SUS, QT_NSUS) para número.
* **População** (`transform/populacao.py`): padroniza os nomes das colunas de cada planilha do IBGE, monta o código de município com 7 dígitos, limpa os valores de população (remove pontos e notas de rodapé), marca a origem de cada ano e calcula 2023 pela média entre 2022 e 2024.
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

O flow do Prefect roda localmente, sem precisar subir um servidor do Prefect antes. Ele executa as mesmas funções do `src/pipeline.py`, organizadas como tarefas.
</details>

<details>
<summary>📦 Por que Parquet em vez de CSV</summary>

Parquet é um formato colunar, mais compacto e mais rápido de ler que CSV, e mantém o tipo de cada coluna salvo junto com o arquivo. Isso evita ter que reconverter tipos toda vez que alguém abre os dados tratados.
</details>

## Como atualizar os dados

<details>
<summary>📆 Incluir um mês novo do SIH ou do CNES</summary>

1. Baixe o arquivo do mês no [DATASUS](https://datasus.saude.gov.br/transferencia-de-arquivos/): `RDGOAAMM.dbc` para o SIH e `LTGOAAMM.dbc` para o CNES (AA é o ano com dois dígitos e MM o mês).
2. Converta o `.dbc` para `.parquet`, mantendo o mesmo nome, e salve na pasta do ano: `data/raw/sih/<ano>/` ou `data/raw/cnes/<ano>/`. Todas as colunas devem ficar como texto, igual aos arquivos que já estão no repositório.
3. Atualize os testes de cobertura temporal (`tests/test_sih.py` e `tests/test_cnes.py`), que conferem a quantidade de meses e o último mês esperado.
4. Rode o pipeline e os testes de qualidade da staging:
   ```bash
   python -m src.pipeline
   pytest tests/test_sih.py tests/test_cnes.py tests/test_populacao.py
   ```
5. Se passarem, copie os três arquivos de `data/staging` para `data/silver` e rode todos os testes:
   ```bash
   cp data/staging/*.parquet data/silver/
   pytest
   ```
</details>

<details>
<summary>🗓️ Incluir um ano novo</summary>

Além dos passos acima:

* Ajuste `ANO_FINAL` em `src/config.py`.
* Inclua a planilha de população do ano em `data/raw/ibge/estimativas/<ano>/` e registre o arquivo e o nome da aba em `ARQUIVOS_IBGE`, no `src/extract/ibge.py`.
* Atualize o teste de cobertura da população (`tests/test_populacao.py`).
</details>

## Solução de problemas

<details>
<summary>⏳ Notebook fica carregando e não executa as células no VS Code</summary>

A versão 7 do `ipykernel` tem um problema conhecido com a extensão Jupyter do VS Code que faz as células ficarem travadas ([issue #17228](https://github.com/microsoft/vscode-jupyter/issues/17228)). Por isso o `requirements.txt` fixa `ipykernel<7`.

Se o problema aparecer, confira a versão instalada:

```bash
pip show ipykernel
```

Se for 7.x, instale a versão 6 e recarregue o VS Code (`Ctrl+Shift+P` e depois `Developer: Reload Window`):

```bash
pip install "ipykernel<7"
```
</details>

<details>
<summary>🧩 O VS Code pede para escolher ou instalar um kernel</summary>

Clique no nome do kernel no canto superior direito do notebook, escolha "Select Another Kernel", depois "Python Environments", e selecione o `.venv` do projeto (Python 3.12). Confira se o `.venv` está ativo e se as dependências foram instaladas com `pip install -r requirements.txt`.
</details>

<details>
<summary>❌ Os testes falham com arquivo não encontrado</summary>

Os testes leem `data/staging`, que é gerada pelo pipeline. Rode `python -m src.pipeline` antes do `pytest`.
</details>

<details>
<summary>❌ Os notebooks 01, 02 ou 04 dão erro logo no começo</summary>

Esses notebooks procuram os arquivos `.dbc`, que não vêm no repositório. Veja [Notebooks que dependem dos arquivos .dbc](#como-funcionam-os-notebooks).
</details>

## Como contribuir

<details>
<summary>🌿 Fluxo de trabalho com Git</summary>

1. Crie uma branch para cada mudança, a partir da `main` atualizada:
   ```bash
   git checkout main
   git pull
   git checkout -b tipo/descricao-curta
   ```
   Exemplos de nome: `fix/config`, `docs/readme`, `feat/analise-idade`.
2. Antes de commitar, confira o que mudou com `git status`.
3. Não suba a pasta `.venv/`, os arquivos de `data/staging/` nem os `.dbc`. Eles já estão no `.gitignore`.
4. Envie a branch e abra um pull request para a `main`:
   ```bash
   git push -u origin nome-da-branch
   ```
</details>

<details>
<summary>📓 Cuidados com os notebooks</summary>

Ao rodar um notebook, o VS Code grava os resultados e a numeração das execuções dentro do arquivo `.ipynb`, e o Git passa a mostrar o notebook como modificado. Se você só rodou o notebook, sem mudar o código, descarte essas alterações antes de commitar:

```bash
git restore notebooks/
```

Esse comando desfaz todas as alterações não commitadas nos notebooks. Se você editou algum de propósito, restaure só os outros, informando o nome de cada arquivo.
</details>

## Perguntas frequentes

<details>
<summary>🐍 Qual linguagem e quais bibliotecas o projeto usa</summary>

Python 3.12, com pandas para manipulação de dados, pyarrow para ler e escrever Parquet, openpyxl e xlrd para ler planilhas do IBGE, prefect para orquestração do pipeline, pytest para os testes e ipykernel para rodar os notebooks. O PySUS é usado para ler os arquivos `.dbc` do DATASUS nos notebooks `01`, `02` e `04`. O duckdb está no `requirements.txt`, mas hoje não é usado no código nem nos notebooks.
</details>

<details>
<summary>🗂️ Existe um dicionário de dados</summary>

Ainda não. Esse é um ponto pendente do projeto: falta uma tabela reunindo nome da coluna, tipo, significado e fonte de cada variável usada.
</details>

<details>
<summary>🔄 O pipeline é repetível do zero</summary>

Em parte. A partir de `data/raw`, a extração e a transformação são scriptadas, então qualquer pessoa do grupo pode rodar `python -m src.pipeline` (ou o flow do Prefect) e reproduzir a staging do início. Duas etapas ainda não são automáticas: o download e a conversão dos `.dbc` para `.parquet`, e a cópia da staging validada para `data/silver`.
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
* 🔄 Script para baixar os `.dbc` do DATASUS e converter para `.parquet`.
* 📓 Adaptar os notebooks `01`, `02` e `04` para lerem os `.parquet` de `data/raw`, sem depender dos `.dbc`.
* ⚙️ Etapa automática que copie a staging validada para `data/silver`.

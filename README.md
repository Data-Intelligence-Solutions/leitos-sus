# GiroSUS · leitos-sus

**GiroSUS** é um produto de dados para gestores do SUS em Goiás: um painel de Power BI para **planejamento** da ocupação de leitos, feito com o dado oficial das internações (SIH/SUS). Este repositório (`leitos-sus`) guarda tudo o que sustenta o produto: o código que trata os dados, as tabelas do painel, os testes e a documentação.

> **Base do produto: só o SIH/SUS.** Todos os números do GiroSUS vêm do SIH/SUS (Sistema de Informações Hospitalares), inclusive o código do hospital, que é a coluna `CNES` do próprio SIH. O IBGE entra só para mostrar o nome dos municípios e não muda nenhum número. O CNES e a população do IBGE foram usados só na exploração (notebooks `02`, `03` e `05`), fora do painel. Veja [Por que só o SIH](#o-produto-girosus).

O GiroSUS mostra **quem ocupa os leitos do SUS em Goiás, por quanto tempo e quanto isso custa**. Ele olha todas as causas de internação e mede tudo em **leito-dia** (um paciente ocupando um leito por um dia).

> **O que é o GiroSUS, em uma frase:** GiroSUS é um painel de Power BI para **planejamento** da ocupação de leitos do SUS em Goiás, feito com dado oficial e mensal das internações (SIH/SUS). **Não é uma ferramenta de gestão de leitos em tempo real.**
>
> **Usamos uma ferramenta de leito?** Não. O GiroSUS não usa censo hospitalar, sistema de regulação nem cadastro de leitos. Ele mede o uso do leito a partir das internações pagas pelo SUS. O CNES (leitos cadastrados) só foi usado na exploração.

> **Em 30 segundos:** os dados do SUS entram em `data/raw`, o código limpa e organiza, os testes conferem, o script `gerar_modelo_bi_girosus.py` monta as tabelas do painel e o Power BI mostra o resultado. O material do produto fica em `docs/`: o painel página por página em [`docs/bi/GiroSUS_modelagem_bi.pdf`](docs/bi/GiroSUS_modelagem_bi.pdf), as medidas DAX em [`docs/bi/GiroSUS_modelagem_dax.pdf`](docs/bi/GiroSUS_modelagem_dax.pdf) e o pitch em [`docs/apresentacao/GiroSUS_pitch.pdf`](docs/apresentacao/GiroSUS_pitch.pdf).

## Integrantes do grupo
* Renata Aires: https://www.linkedin.com/in/renata-aires-saraiva
* João Vitor: https://www.linkedin.com/in/jvfmagalhaes?utm_source=share_via&utm_content=profile&utm_medium=member_android
* Lucas Parisotto: https://www.linkedin.com/in/lucas-parisotto-0ab7a93b5?utm_source=share_via&utm_content=profile&utm_medium=member_ios
* Felipe Barbosa:
* Ana Ruy: https://www.linkedin.com/in/ruyluques/

## Sumário

* [O produto GiroSUS](#o-produto-girosus)
  * [Como lidamos com a defasagem](#como-lidamos-com-a-defasagem)
* [Onde está cada coisa](#onde-está-cada-coisa)
* [Como rodar o projeto](#como-rodar-o-projeto)
* [Como os dados andam](#como-os-dados-andam)
* [Regras de negócio](#regras-de-negócio)
* [Modelo do Power BI](#modelo-do-power-bi)
* [Dicionário de dados](#dicionário-de-dados)
* [Notebooks](#notebooks)
* [Testes](#testes)
* [Como atualizar os dados](#como-atualizar-os-dados)
* [Solução de problemas](#solução-de-problemas)
* [Como contribuir](#como-contribuir)
* [Perguntas frequentes](#perguntas-frequentes)
* [Bases de dados e fontes](#bases-de-dados-e-fontes)
* [Referências e benchmarks](#referências-e-benchmarks)
* [Status do projeto](#status-do-projeto)

## O produto GiroSUS

<details>
<summary>🎯 O que é e qual problema resolve</summary>

Contar internações esconde o que realmente pesa na rede: um paciente que fica 30 dias ocupa o mesmo leito que dez pacientes de 3 dias. Por isso o GiroSUS mede em **leito-dia** e mostra quem ocupa os leitos, por quanto tempo e quanto o SUS paga por eles. O nome vem de “giro de leito”, o indicador de quantas vezes um leito recebe um paciente novo.

Por que isso importa: o SUS paga um pacote fixo por procedimento. Então cada dia a mais de internação, além do necessário, é um leito a menos para outro paciente e um custo que o hospital banca sozinho.

O painel serve para **planejar**, não para achar vaga agora: o dado do SUS chega com 1 a 2 meses de atraso. Veja [Como lidamos com a defasagem](#como-lidamos-com-a-defasagem).

**Para quem:** diretores de hospital, Secretaria Estadual de Saúde e secretarias municipais.
</details>

<details>
<summary>🏥 Por que só o SIH</summary>

O SIH é a única base que tem, numa linha só, **tudo o que o produto mede**: datas de entrada e saída, dias internado, diagnóstico, procedimento, hospital, cidade do paciente e valor pago pelo SUS. Com ele se calcula leito-dia, tempo típico, custo e fluxo entre cidades sem cruzar com outra fonte.

| Base | Papel no projeto | Entra no GiroSUS? |
|---|---|---|
| **SIH/SUS** (internações) | Base do produto | ✅ Sim, todos os números |
| **IBGE** (população) | Tabela de apoio | Só os nomes dos municípios |
| **CNES** (leitos) | Exploração (notebooks `02` e `05`) | ❌ Não |

Por que o CNES ficou de fora: ele diz quantos leitos estão **cadastrados**, não quem os ocupa. Leito cadastrado não é leito em operação, e cruzar as duas bases exigiria premissas que o painel não precisa para responder as suas perguntas.

**Por que o painel não mostra o nome do hospital, e qual o impacto.** O SIH não traz o nome do hospital: traz o código CNES, que é o identificador oficial de cada estabelecimento no país. Como o GiroSUS usa só o SIH, o hospital aparece como "código · município" (ex.: `7743068 · Goiânia`). Foi uma decisão: uma base oficial só, sem cadastro extra para baixar e manter, e sem risco de ligar um hospital ao nome errado ou de deixar o nome em branco.

* **Impacto nos números: nenhum.** Todos os indicadores por hospital (leitos-dia, dias acima do típico, R$ por dia) são calculados pelo código CNES, e os 260 hospitais da safra 2025 têm código e município.
* **Impacto na leitura:** o gestor vê o código em vez do nome. O diretor conhece o CNES do próprio hospital, e qualquer código pode ser consultado no site público do CNES ([cnes.datasus.gov.br](https://cnes.datasus.gov.br/)).
* **Se o cliente quiser os nomes:** dá para acrescentar depois o cadastro de estabelecimentos do CNES como tabela de apoio, sem mudar nenhum número.
</details>

<details>
<summary>📦 Base, safra e números principais</summary>

* **Base:** só o SIH/SUS (`data/silver/sih_multianual.parquet`).
* **Safra:** competências de janeiro a dezembro de 2025, só AIH regular (IDENT = 1). A tendência de 2022 a 2025 fica na tabela `tendencia_anual` (média de internados por dia em cada ano).
* **Números de 2025:** 457.403 internações, 1.835.227 leitos-dia, R$ 726,1 milhões pagos, permanência média de 4,0 dias e R$ 396 por leito-dia.
</details>

<details>
<summary>📈 O que o painel já mostra</summary>

* O respiratório é só a 4ª causa de internação, mas a 2ª que mais ocupa leito (12,5% dos leitos-dia e 8,9% do valor pago). O circulatório é o contrário: 11,9% dos leitos e 21% do valor.
* Internações de mais de 15 dias são 4,4% dos pacientes, mas ocupam 27,3% dos leitos-dia.
* 43,9% dos leitos-dia ficaram acima do tempo típico do procedimento. Reduzir 10% desses dias equivale a cerca de 20 mil internações a mais por ano, com os mesmos leitos.
* Goiânia concentra 44,7% dos leitos-dia do estado, e 56,6% deles são usados por moradores de outras cidades.

* **Tendência:** a rede cresce todo ano. Média de pacientes internados por dia: 4.398 em 2022, 4.734 em 2023 (+7,6%), 4.854 em 2024 (+2,5%) e 5.053 em 2025 (+4,1%).

Antes do GiroSUS, o projeto fez uma análise só de doenças respiratórias (continua no histórico do Git). Ela mostrou que essas internações são cerca de 9% do total em Goiás, com pico entre abril e junho; que municípios menores têm mais internação por habitante; e que, comparadas às demais, têm mais que o dobro de mortalidade, ficam mais tempo e usam UTI quase duas vezes mais.
</details>

<details>
<summary>⏱️ Como lidamos com a defasagem</summary>

#### Como lidamos com a defasagem

O SIH chega com 1 a 2 meses de atraso: o hospital apresenta a conta (AIH) no mês da alta ou nos meses seguintes. O GiroSUS lida com isso em quatro camadas:

1. **Transparência** (próxima etapa): o painel vai mostrar a data de corte e marcar cada mês como *fechado*, *em consolidação* ou *estimado*. Assim o gestor sempre sabe o que já está completo.
2. **Decisão baseada em mês fechado** (já no painel): os números principais, como os leitos presos além do típico e o simulador, usam a safra fechada. A defasagem não muda a decisão, só atrasa o mês mais recente.
3. **Estimativa dos meses incompletos** (testada com dado real): o atraso da cobrança é estável (65% das internações chegam no mesmo mês da alta e 99% em até 3 meses). Por isso dá para completar os meses recentes. Testado com 2025: no mês mais recente, erro de 8,4%, contra 29% olhando só o que chegou; um mês antes, erro de 2,7%. Entra no painel como "estimado", com faixa de erro.
4. **Atualização mensal** (próxima etapa): todo mês o estimado vai virar real, e o painel vai mostrar quanto errou (o placar de acerto). Opção de piloto: o hospital contratante pode mandar os dados dele do mês corrente, para ver o "agora" dele mesmo.

**Gestão de custo com a defasagem.** Regra: **custo estimado do mês = leitos-dia estimados × R$ por leito-dia dos últimos 3 meses fechados, calculado por grupo de doença.** Por grupo e com meses recentes porque o R$ por leito-dia é estável, mas não é fixo: em 2025 variou entre R$ 361 e R$ 427 por mês e subiu no segundo semestre. Uma média do ano inteiro puxaria o valor para trás. Testado com 2025: erro de 4,8% no mês mais recente (contra 32,2% olhando só o que chegou) e de 4,0% um mês antes.

**Onde terei leito disponível?** O GiroSUS não diz onde há leito livre hoje. Ele mostra **quando e onde a pressão é menor**: dezembro e janeiro são os meses mais vazios (−4,9% e −3,4% da média do ano), o fim de semana tem menos entradas (cerca de 940 por dia, contra 1.435 na terça) e há hospitais e municípios com menos dias acima do típico. Para ir além, dá para cruzar com o CNES (leitos SUS cadastrados) e estimar a taxa de ocupação por hospital, com um aviso: leito cadastrado não é leito em operação.

**Situação hoje:** o painel usa a safra 2025 completa, com todos os meses fechados. A estimativa dos meses incompletos e do custo já foi testada com os dados de 2025 e entra no painel com a atualização mensal, junto com a marcação de cada mês e o placar de acerto. Para repetir o teste:

```bash
python testar_estimativa_defasagem.py
```

Ele mede o atraso da cobrança, refaz as estimativas de 2025 "voltando no tempo" e para com ERRO se algum número do slide mudar.
</details>

## Onde está cada coisa

<details>
<summary>📄 Os materiais do projeto e para quem é cada um</summary>

| Material | Onde está | Para quem |
|---|---|---|
| Pitch curto do produto, em 2 páginas | `docs/apresentacao/GiroSUS_pitch.pdf` | Clientes, quem apresenta e avaliadores |
| Análise com todos os números do GiroSUS | `notebooks/06_girosus_ocupacao_leitos.ipynb` | Analistas |
| Tabelas que o Power BI importa (10 arquivos `.csv`) | geradas por `gerar_modelo_bi_girosus.py` em `data/gold/girosus/` | Analista de BI |
| O que significa cada coluna | seção [Dicionário de dados](#dicionário-de-dados) e `docs/dicionário/GiroSUS_dicionario_dados.csv` | Todo mundo |
| Como o código funciona, pasta por pasta, e a lista de todos os tratamentos feitos nos dados | `docs/code/GiroSUS_como_funciona.pdf` | Quem vai mexer no código |
| Material de negócio do painel: cada gráfico, a pergunta que responde (P7 a P40), as regras e a defasagem | `docs/bi/GiroSUS_modelagem_bi.pdf` | Quem apresenta e o cliente |
| Todas as medidas DAX, por página e pergunta | `docs/bi/GiroSUS_modelagem_dax.pdf` | Analista de BI |
| Teste da estimativa dos meses incompletos (defasagem) | `testar_estimativa_defasagem.py` | Quem precisa provar os números da defasagem |
</details>

<details>
<summary>🗂️ As pastas e o que cada uma faz</summary>

```
leitos-sus/
├── 📊 dashboard/                  # Pasta reservada (hoje vazia; o material do produto está em docs/)
├── 🗂️ data/
│   ├── raw/                        # Dados originais: SIH (base do produto); CNES e IBGE (exploração e apoio)
│   ├── staging/                    # O que o pipeline gera (fica só na sua máquina, não vai para o Git)
│   ├── silver/                     # Bases conferidas pelos testes; é daqui que as análises leem
│   └── gold/girosus/               # Tabelas do Power BI em CSV (geradas na sua máquina, fora do Git)
├── 📖 docs/
│   ├── apresentacao/               # GiroSUS_pitch.pdf: o pitch curto
│   ├── bi/                         # GiroSUS_modelagem_bi.pdf (negócio) e GiroSUS_modelagem_dax.pdf (medidas DAX)
│   ├── dicionário/                 # GiroSUS_dicionario_dados.csv: o dicionário em planilha
│   └── code/                       # GiroSUS_como_funciona.pdf: explicação do código e lista dos tratamentos
├── 📓 notebooks/                   # Exploração e análises (06_girosus_ocupacao_leitos = GiroSUS)
├── 🐍 src/
│   ├── config.py                   # Caminhos e parâmetros (anos, estado) num lugar só
│   ├── converter_dbc.py            # Converte os .dbc do DATASUS em .parquet (data/raw)
│   ├── pipeline.py                 # Roda o ETL: extrai, padroniza e grava na staging
│   ├── promover_silver.py          # Testa a staging e, se passar, copia para a silver
│   ├── extract/                    # Lê os arquivos de cada fonte (SIH, CNES, IBGE)
│   ├── transform/                  # Padroniza os dados de cada fonte
│   └── orchestration/              # O mesmo pipeline, organizado com Prefect
├── ✅ tests/                       # Testes de qualidade (pytest)
├── gerar_modelo_bi_girosus.py      # Monta as tabelas do Power BI em data/gold/girosus
├── testar_estimativa_defasagem.py  # Testa a estimativa dos meses incompletos (defasagem do SIH)
├── requirements.txt                # Bibliotecas do projeto
└── README.md                       # Este arquivo
```
</details>

## Como rodar o projeto

Você precisa do **Python 3.12**. Todos os comandos abaixo são para o terminal Git Bash, na pasta raiz do projeto.

<details>
<summary>1️⃣ Preparar o ambiente (só na primeira vez)</summary>

```bash
# Cria o ambiente virtual (uma "caixinha" com as bibliotecas do projeto)
py -3.12 -m venv .venv

# Ativa o ambiente (faça isso sempre que abrir um terminal novo)
source .venv/Scripts/activate

# Instala as bibliotecas
pip install -r requirements.txt
```

Deu erro? Veja [O ambiente não instala ou dá erro](#solução-de-problemas).
</details>

<details>
<summary>2️⃣ Gerar as tabelas do painel GiroSUS (o principal)</summary>

Com o ambiente ativo:

```bash
python gerar_modelo_bi_girosus.py
```

O que acontece: o script lê `data/silver`, aplica as regras do GiroSUS e grava as **10 tabelas do Power BI em `.csv`** em `data/gold/girosus/`. Leva cerca de 1 minuto e meio. Se houver `.parquet` antigos nessa pasta, o script apaga, para ninguém se confundir.

Os CSVs usam o padrão brasileiro: separador `;` e decimal `,` (por exemplo, `485,78`). O Excel e o Power BI em português abrem direto. Feche esses arquivos no Excel antes de rodar, senão o script não consegue regravar e avisa.

No final, ele confere se os 10 CSVs existem com todas as colunas e imprime a conferência da safra 2025. Esses números precisam bater com o `docs/bi/GiroSUS_modelagem_bi.pdf` e com o notebook 06: **457.403 internações, 1.835.227 leitos-dia, R$ 726,1 milhões e 43,9% dos leitos-dia acima do típico**.

Rode de novo sempre que `data/silver` for atualizada.
</details>

<details>
<summary>3️⃣ Abrir os notebooks</summary>

Abra a pasta do projeto no VS Code. O arquivo `.vscode/settings.json` já escolhe o Python do `.venv`, e o `ipykernel` vem no `requirements.txt`, então não precisa instalar nem escolher kernel na mão.
</details>

<details>
<summary>4️⃣ Refazer as bases do zero (opcional)</summary>

Só é preciso se você mudou algo em `data/raw` ou em `src/`. O passo a passo completo está em [Como atualizar os dados](#como-atualizar-os-dados).
</details>

## Como os dados andam

```
DATASUS (.dbc)  ──src/converter_dbc.py──▶  data/raw/sih, data/raw/cnes (.parquet)
IBGE (.xls/.xlsx) ───────────▶  data/raw/ibge
                                     │
                                     ▼
                         src/pipeline.py (ETL)
                                     │
                                     ▼
                         data/staging/*.parquet
                                     │  src/promover_silver.py (testa e copia)
                                     ▼
                         data/silver/*.parquet
                                     │
                                     ▼
                      notebooks 05 e 06 (análises)
                                     │
                                     ▼
                  gerar_modelo_bi_girosus.py (regras do GiroSUS)
                                     │
                                     ▼
                      data/gold/girosus/*.csv
                                     │
                                     ▼
                       Power BI (painel GiroSUS)
```

<details>
<summary>🔎 Quem faz cada etapa</summary>

| Etapa | Onde acontece | Resultado |
|---|---|---|
| Baixar os arquivos mensais do SIH (RD) e do CNES (LT) | À mão, no site do DATASUS | Arquivos `.dbc` |
| Converter `.dbc` para `.parquet` | `python -m src.converter_dbc` (usa o PySUS; só converte o que ainda não tem `.parquet`) | `data/raw/sih/<ano>/RDGO*.parquet` e `data/raw/cnes/<ano>/LTGO*.parquet` |
| Baixar as planilhas de população | À mão, no FTP do IBGE | `data/raw/ibge/...` |
| Extrair e padronizar | `python -m src.pipeline` ou o flow do Prefect (mostra na tela cada base gravada) | `data/staging/*.parquet` |
| Conferir e promover para silver | `python -m src.promover_silver`: roda os testes de qualidade e, só se passarem, copia a staging para a silver e confere se ficaram iguais | `data/silver/*.parquet` |
| Analisar | Notebooks `05` e `06` | Leem só `data/silver` |
| Montar as tabelas do painel | `python gerar_modelo_bi_girosus.py` | `data/gold/girosus/*.csv` |
| Painel | Power BI, seguindo `docs/bi/GiroSUS_modelagem_bi.pdf` (gráficos) e `docs/bi/GiroSUS_modelagem_dax.pdf` (medidas) | Relatório GiroSUS |
</details>

<details>
<summary>⚙️ O que o pipeline faz com cada fonte</summary>

O pipeline trata as três bases, porque elas alimentam as análises exploratórias. O GiroSUS, porém, lê só a silver do SIH (e os nomes de municípios do IBGE).

Cada fonte (SIH, CNES, IBGE) passa por três passos, cada um na sua pasta dentro de `src/`:

1. **`extract/`**: lê os arquivos de `data/raw` e carrega numa tabela (DataFrame), sem mudar nada. No SIH e no CNES, lê os `.parquet` mensais dos anos definidos em `src/config.py` e anota o nome do arquivo de origem. No IBGE, lê as planilhas de população de cada ano.
2. **`transform/`**: padroniza os dados:
   * **SIH** (`transform/sih.py`): transforma a data de internação (DT_INTER) em data. O resto fica como veio.
   * **CNES** (`transform/cnes.py`): tira o ano e o mês do nome do arquivo (`LTGO2401` vira 2024, mês 1) e transforma as quantidades de leitos (QT_EXIST, QT_SUS, QT_NSUS) em número.
   * **População** (`transform/populacao.py`): padroniza os nomes das colunas de cada planilha, monta o código de município com 7 dígitos, limpa os valores (tira pontos e notas de rodapé), marca a origem de cada ano e calcula 2023 pela média entre 2022 e 2024.
3. **Grava** o resultado em Parquet em `data/staging` e mostra na tela quantas linhas e colunas cada base teve.

O pipeline **não** grava em `data/silver`. Quem faz isso é o `src/promover_silver.py`, e só depois que os testes passam.
</details>

<details>
<summary>📦 Parquet por dentro, CSV na entrega</summary>

Nas camadas internas (raw, staging e silver), o projeto usa Parquet: é compacto, rápido de ler e guarda o tipo de cada coluna, então ninguém precisa reconverter datas e números. Só a saída do painel (`data/gold/girosus/`) é em CSV, porque é o formato que o time de BI usa no Power BI e no Excel.
</details>

<details>
<summary>📁 Arquivos que não vêm no repositório</summary>

Estes itens estão no `.gitignore` e não aparecem num `git clone`:

* `*.dbc`: arquivos originais do DATASUS. O repositório já traz a versão em `.parquet`, que é a que o pipeline usa.
* `data/raw/ibge/censo_2022/Pessoas_52_publico.csv`: microdados do Censo, grandes demais e fora da base final.
* `*.dbf`: arquivo temporário que o PySUS cria durante a conversão.
* `data/staging/`: aparece quando você roda o pipeline.
* `data/gold/girosus/`: as tabelas do painel. O CSV da fato passa de 250 MB, acima do limite do GitHub (100 MB); cada pessoa gera o seu com o script.
* `.venv/`: o ambiente virtual de cada pessoa.

A pasta `docs/` (dicionário em CSV e os PDFs) **vai** para o Git.
</details>

## Regras de negócio

<details>
<summary>🏥 O que é uma AIH e quais entram na conta</summary>

AIH é a Autorização de Internação Hospitalar, o documento que registra cada internação no SUS. Existem dois tipos:

* **IDENT = 1 (regular):** uma internação nova. É essa que entra na conta.
* **IDENT = 5 (longa permanência):** continuação de uma internação que já existe. Fica de fora, porque contaria o mesmo paciente duas vezes.
</details>

<details>
<summary>📅 Período: por que vai só até junho de 2026</summary>

O projeto cobre janeiro de 2021 a junho de 2026. Como 2026 ainda está em andamento, ele entra parcial, e comparações de volume e sazonalidade usam só os anos completos (2021 a 2025).

As bases não terminam no mesmo mês: o SIH vai até junho de 2026 e o CNES até julho de 2026. Nas análises, as internações são cortadas pela data de internação, entre 01/01/2021 e 30/06/2026.
</details>

<details>
<summary>📍 Recorte geográfico</summary>

O foco é Goiás (UF GO, código IBGE 52): internações em hospitais goianos. No notebook `05`, que calcula indicadores por população (internações por 10 mil habitantes), entram só pacientes que moram em municípios goianos.
</details>

<details>
<summary>🩺 Grupos de doença</summary>

O GiroSUS agrupa as internações pela primeira letra do diagnóstico principal (DIAG_PRINC), que é o capítulo da CID-10. Exemplos: J = Respiratório, I = Circulatório, S e T = Lesões e traumas, D00 a D48 = Câncer, D50 a D89 = Sangue. A lista completa de grupos está na tabela `dim_diagnostico` do [Dicionário de dados](#dicionário-de-dados).
</details>

<details>
<summary>🗓️ Por que a população vem de várias publicações do IBGE (base de apoio)</summary>

Não existe uma única fonte do IBGE com todos os anos, então o projeto junta várias:

* **2021:** estimativa anual do IBGE (`estimativas/2021`).
* **2022:** população do Censo 2022, na versão enviada ao TCU (`tcu_2023`).
* **2023:** o IBGE não publicou. O projeto calcula a média entre 2022 e 2024 e marca a origem como "Cálculo próprio com dados IBGE".
* **2024, 2025 e 2026:** estimativas anuais do IBGE (`estimativas/2024`, `2025`, `2026`).

Nem tudo em `data/raw/ibge` é usado: os microdados do Censo em `censo_2022/` e o arquivo por UF em `tcu_2023/POP_TCU_2023_Brasil_e_UFs...` foram baixados só como referência.

No SIH e no CNES não tem esse problema: é a mesma fonte mês a mês, e todos os arquivos do período são usados.
</details>

<details>
<summary>📌 Onde essas regras são aplicadas</summary>

As regras **não** ficam no pipeline. O `src/` só lê e padroniza, mantendo todas as AIHs. As regras entram depois:

* Tirar as AIHs de continuação (IDENT = 5), cortar o período e filtrar residentes em Goiás: notebooks `05` e `06`.
* Regras do GiroSUS (safra, grupo de doença, tempo típico, dias acima do típico): notebook `06` e `gerar_modelo_bi_girosus.py`, com a mesma lógica nos dois.

Vai criar um indicador novo? Aplique os mesmos filtros, senão seus números não vão bater com os do projeto.
</details>

## Modelo do Power BI

O script `gerar_modelo_bi_girosus.py` (veja [Como rodar o projeto](#como-rodar-o-projeto)) entrega 2 tabelas fato (os acontecimentos), 6 dimensões (as “legendas” usadas nos filtros) e 2 tabelas de apoio (sazonalidade e tendência), sem relacionamento.

<details>
<summary>🗃️ As tabelas geradas</summary>

| Arquivo | Cada linha é | Linhas |
|---|---|---|
| `fato_internacoes` | Uma internação (AIH regular) da safra 2025 | 457.403 |
| `fato_ocupacao_diaria` | Um hospital, num dia de 2025, num grupo de doença (internados, entradas e altas) | 392.172 |
| `dim_tempo` | Um dia do calendário (17/05/2024 a 31/12/2025: a 1ª internação da safra 2025 até o fim de 2025) | 594 |
| `dim_diagnostico` | Um código CID-10, com o grupo de doença | 6.114 |
| `dim_procedimento` | Um procedimento da tabela SIGTAP | 1.346 |
| `dim_hospital` | Um hospital (CNES) | 260 |
| `dim_municipio_residencia` e `dim_municipio_atendimento` | Um município (mesma tabela, uma para cada lado da relação) | 1.241 |
| `sazonalidade_mensal` | Um mês de 2025 num grupo de doença, mais a linha "Total da rede" (tabela de apoio, sem relacionamento; um mapa de calor de sazonalidade) | 252 |
| `tendencia_anual` | Um ano (2022 a 2025) com a média de pacientes internados por dia (tabela de apoio, sem relacionamento; a tendência da P29) | 4 |

* Todas saem em `.csv` (separador `;`, decimal `,`).
* **Importação pronta:** o script também grava `data/gold/girosus/power_query/<tabela>.pq`, uma consulta por tabela. Ela já lê o `;` e o decimal `,` (pt-BR) e já deixa `cnes`, `proc_rea`, `cid`, `codigo`, `munic_residencia` e `munic_atendimento` como **Texto**, sem perder o zero da frente (`0965324` não vira `965324`). No Power BI: Obter dados > Consulta nula > Editor avançado, cole o conteúdo do `.pq` e renomeie a consulta com o nome da tabela. Repita para as 10 tabelas.
* O caminho do `.csv` dentro do `.pq` é o da pasta onde o script rodou. Se o projeto mudar de pasta, rode o script de novo (ou ajuste a linha `Arquivo`).
* **Tudo olha só para a safra 2025**, como o `GiroSUS_modelagem_bi.pdf`. A ocupação diária usa também as AIHs cobradas em 2024 e 2026 para contar quem estava internado nos dias de 2025, e depois fica só com os dias de 2025.
* O script para com ERRO se qualquer célula de qualquer tabela vier vazia.
* Em `dim_procedimento.csv`, `nome_procedimento` traz 8 nomes definidos no script. Os demais vêm como `Procedimento <código>`, porque nenhuma base local (SIH, CNES, IBGE) tem o nome do procedimento. Se você trocar à mão pelo nome da tabela SIGTAP, o script preserva na próxima execução.
* O SIH não tem o nome do hospital. O hospital vem da coluna `CNES` do SIH (código do Cadastro Nacional de Estabelecimentos de Saúde, 7 dígitos), e os arquivos de leitos do CNES do projeto (`LTGO*`) também não têm o nome. Por isso `dim_hospital.csv` identifica o hospital pelo `cnes` e pelo município e **não tem** `nome_hospital` (a coluna sairia vazia; o script para com erro se ela aparecer).
* O valor da UTI (`VAL_UTI`) ainda não está na silver, então o script lê direto de `data/raw/sih`. Se esses arquivos não estiverem na máquina, o script para com erro (em vez de gerar `valor_uti` vazio).

O que é cada coluna: [Dicionário de dados › Tabelas do painel GiroSUS](#dicionário-de-dados).
</details>

<details>
<summary>🔗 Relacionamentos e montagem no Power BI</summary>

Relacionamentos (todos 1 para muitos e ativos):

* `dim_tempo[data]` → `fato_internacoes[data_internacao]` e `fato_ocupacao_diaria[data]`
* `dim_hospital[cnes]` → `fato_internacoes[cnes]` e `fato_ocupacao_diaria[cnes]`
* `dim_diagnostico[cid]` → `fato_internacoes[cid]`
* `dim_procedimento[proc_rea]` → `fato_internacoes[proc_rea]`
* `dim_municipio_residencia[codigo]` → `fato_internacoes[munic_residencia]`
* `dim_municipio_atendimento[codigo]` → `fato_internacoes[munic_atendimento]`

Depois de importar:

* Marque `dim_tempo` como tabela de datas.
* Classifique `nome_mes` por `mes`, `nome_dia` por `dia_semana` e `faixa_duracao` por `ordem_faixa`.
* Filtre `fato_internacoes[safra] = 2025` nas páginas 1 a 6 e `dim_tempo[ano] = 2025` na página do calendário (a safra não filtra a tabela de ocupação).
* Crie o parâmetro **Redução %** (de 0,05 a 0,30).

Todas as medidas DAX, organizadas pela página e pela pergunta, com o resultado esperado de cada uma, estão em `docs/bi/GiroSUS_modelagem_dax.pdf`. O gráfico de cada página está em `docs/bi/GiroSUS_modelagem_bi.pdf`.
</details>

## Dicionário de dados

O dicionário é a “legenda” das nossas tabelas: para cada coluna, diz o que ela significa, de onde veio, que tipo de valor tem e um exemplo real. Ele está aqui embaixo para ler e também em [`docs/dicionário/GiroSUS_dicionario_dados.csv`](docs/dicion%C3%A1rio/GiroSUS_dicionario_dados.csv), para abrir no Excel e filtrar.

<details>
<summary>📖 Para que serve (com exemplos)</summary>

Os arquivos do DATASUS vêm com nomes curtos e códigos que não dizem nada sozinhos. O dicionário traduz:

| Você vê na tabela | O que quer dizer |
|---|---|
| `VAL_TOT = 485.78` | Valor total pago pelo SUS pela internação, em R$ (não é o custo real do hospital) |
| `MUNIC_MOV = 520870` | Município onde fica o hospital, em código IBGE de 6 dígitos (520870 = Goiânia) |
| `CAR_INT = 02` | Internação de urgência (01 seria eletiva, ou seja, planejada) |
| `IDENT = 5` | Continuação de uma internação que já existe (por isso fica fora das contagens) |

Use sempre que for criar um indicador, montar um gráfico ou explicar um número numa apresentação.

Ele cobre 105 colunas: SIH (23, a base do produto), as tabelas do painel (60), e também CNES (12) e IBGE (10), que existem no projeto como bases de exploração e apoio.
</details>

<details>
<summary>💡 Como ler e dicas para não errar</summary>

* **Camada:** `silver` = bases tratadas (`data/silver`); `gold` = tabelas do painel (`data/gold/girosus`).
* **Origem:** o campo do arquivo original do DATASUS (RD = internações do SIH; LT = leitos do CNES) ou a regra usada para criar a coluna.
* **Número guardado como texto:** “texto (número)” quer dizer que é número, mas vem como texto. Converta antes de somar (em pandas: `pd.to_numeric(df["VAL_TOT"])`). As tabelas do GiroSUS já vêm convertidas.
* **A idade depende de outra coluna:** `IDADE = 3` pode ser 3 anos, 3 meses ou 3 dias. Quem diz é `COD_IDADE`.
* **`SEXO`, `IDADE`, `COD_IDADE` e `GESTAO`:** saem do pipeline e chegam em `data/silver` quando você roda `python -m src.promover_silver`. Se a sua silver for antiga, rode o pipeline e a promoção (veja [Como atualizar os dados](#como-atualizar-os-dados)).
* **Mantenha em dia:** criou, renomeou ou removeu uma coluna? Atualize esta seção e o CSV na mesma branch da mudança.
</details>

<details>
<summary>🏥 SIH, internações (silver) · base do produto</summary>

Arquivo: `data/silver/sih_multianual.parquet` · 1 linha = 1 AIH (inclui as de continuação) · 2.286.755 registros, competências de jan/2021 a jun/2026, hospitais de Goiás.

| Coluna | Tipo | O que é | Origem / regra | Exemplo |
|---|---|---|---|---|
| `ANO_CMPT` | texto | Ano da competência: ano em que o hospital apresentou a AIH para pagamento | SIH (RD) | `2025` |
| `MES_CMPT` | texto | Mês da competência, com 2 dígitos | SIH (RD) | `05` |
| `N_AIH` | texto | Número da AIH. Identifica a internação, não a pessoa | SIH (RD) | `5220103703310` |
| `IDENT` | texto | Tipo da AIH. Ver códigos | SIH (RD) | `1` |
| `SEQ_AIH5` | texto | Sequencial da AIH de longa permanência. Em Goiás vem sempre 000 | SIH (RD) | `000` |
| `CNES` | texto | Código do hospital no Cadastro Nacional de Estabelecimentos de Saúde (7 dígitos) | SIH (RD) | `6665322` |
| `MUNIC_RES` | texto | Município onde o paciente mora (código IBGE de 6 dígitos, sem o dígito verificador) | SIH (RD) | `521930` |
| `MUNIC_MOV` | texto | Município onde fica o hospital, 6 dígitos | SIH (RD) | `520870` |
| `DT_INTER` | data | Data de entrada no hospital | SIH (RD); vira data em `src/transform/sih.py` | `2025-01-25` |
| `DT_SAIDA` | texto | Data de saída (alta, transferência ou óbito), no formato AAAAMMDD | SIH (RD) | `20250204` |
| `DIAS_PERM` | texto (número) | Dias de permanência. É o leito-dia da internação | SIH (RD) | `3` |
| `UTI_MES_TO` | texto (número) | Total de dias em UTI. 0 = não usou UTI | SIH (RD) | `0` |
| `VAL_TOT` | texto (número) | Valor total pago pelo SUS, em R$. Não é o custo real do hospital | SIH (RD) | `485.78` |
| `DIAG_PRINC` | texto | Diagnóstico principal pela CID-10. A 1ª letra é o capítulo (J = respiratório, I = circulatório…) | SIH (RD) | `J189` |
| `MORTE` | texto | Se o paciente morreu na internação. Ver códigos | SIH (RD) | `0` |
| `ESPEC` | texto | Especialidade do leito. Ver códigos | SIH (RD) | `03` |
| `PROC_REA` | texto | Procedimento realizado, pela tabela SIGTAP (10 dígitos). Define o valor pago | SIH (RD) | `0303140151` |
| `CAR_INT` | texto | Caráter da internação (eletiva, urgência, acidente). Ver códigos | SIH (RD) | `02` |
| `SEXO` | texto | Sexo do paciente. Ver códigos | SIH (RD) · chega na silver com `src.promover_silver` | `3` |
| `IDADE` | texto (número) | Idade, na unidade indicada por COD_IDADE | SIH (RD) · chega na silver com `src.promover_silver` | `27` |
| `COD_IDADE` | texto | Unidade da idade (dias, meses, anos). Ver códigos | SIH (RD) · chega na silver com `src.promover_silver` | `4` |
| `GESTAO` | texto | Tipo de gestão do hospital. Ver códigos | SIH (RD) · chega na silver com `src.promover_silver` | `1` |
| `ARQUIVO_ORIGEM` | texto | Arquivo mensal do DATASUS de onde veio a linha (RDGO + AAMM) | Criada em `src/extract/sih.py` | `RDGO2505.dbc` |
</details>

<details>
<summary>🛏️ CNES, leitos (silver) · exploração, fora do GiroSUS</summary>

Arquivo: `data/silver/cnes_multianual.parquet` · 1 linha = 1 tipo de leito de 1 estabelecimento em 1 mês · 198.448 registros, jan/2021 a jul/2026.

| Coluna | Tipo | O que é | Origem / regra | Exemplo |
|---|---|---|---|---|
| `CNES` | texto | Código do estabelecimento (7 dígitos) | CNES (LT) | `9331603` |
| `CODUFMUN` | texto | Município do estabelecimento (código IBGE de 6 dígitos) | CNES (LT) | `520010` |
| `TP_UNID` | texto | Tipo de unidade (hospital geral, especializado, unidade mista…). Ver códigos | CNES (LT) | `05` |
| `TP_LEITO` | texto | Grande tipo de leito (cirúrgico, clínico, UTI…). Ver códigos | CNES (LT) | `2` |
| `CODLEITO` | texto | Tipo detalhado do leito (ex.: 33 clínica geral, 75 UTI adulto tipo II) | CNES (LT) | `33` |
| `QT_EXIST` | número | Leitos existentes daquele tipo | CNES (LT); vira número em `src/transform/cnes.py` | `9` |
| `QT_SUS` | número | Desses, quantos atendem o SUS | CNES (LT); vira número | `9` |
| `QT_NSUS` | número | Leitos não SUS (planos e particulares) | CNES (LT); vira número | `0` |
| `COMPETEN` | texto | Mês de referência, no formato AAAAMM | CNES (LT) | `202101` |
| `ARQUIVO_ORIGEM` | texto | Arquivo mensal de origem (LTGO + AAMM) | Criada em `src/extract/cnes.py` | `LTGO2101.dbc` |
| `ANO` | número | Ano da competência, tirado do nome do arquivo | Criada em `src/transform/cnes.py` | `2021` |
| `MES` | número | Mês da competência, tirado do nome do arquivo | Criada em `src/transform/cnes.py` | `1` |
</details>

<details>
<summary>👥 IBGE, população (silver) · apoio: no GiroSUS, só nomes de municípios</summary>

Arquivo: `data/silver/populacao_multianual.parquet` · 1 linha = 1 município em 1 ano · 33.422 registros, todos os municípios do Brasil, 2021 a 2026.

| Coluna | Tipo | O que é | Origem / regra | Exemplo |
|---|---|---|---|---|
| `uf` | texto | Sigla do estado | IBGE | `GO` |
| `cod_uf` | texto | Código do estado (2 dígitos). Goiás = 52 | IBGE | `52` |
| `cod_municipio` | texto | Parte do código do município dentro do estado (5 dígitos) | IBGE | `08707` |
| `municipio` | texto | Nome do município | IBGE | `Goiânia` |
| `populacao` | número inteiro | População no ano de referência | IBGE; limpa em `src/transform/populacao.py` | `1503256` |
| `codigo_ibge_7` | texto | Código IBGE completo (7 dígitos). Os 6 primeiros batem com o SIH e o CNES | cod_uf + cod_municipio | `5208707` |
| `ano_referencia` | número | Ano a que a população se refere (2021 a 2026) | Criada em `src/transform/populacao.py` | `2025` |
| `ano_publicacao` | número | Ano em que o IBGE publicou. Vazio em 2023 (valor calculado pelo projeto) | Criada em `src/transform/populacao.py` | `2025` |
| `origem` | texto | IBGE ou “Cálculo próprio com dados IBGE” (2023) | Criada em `src/transform/populacao.py` | `IBGE` |
| `tipo_dado` | texto | Tipo da fonte: estimativa anual, Censo 2022 (TCU) ou interpolação 2022 a 2024 | Criada em `src/transform/populacao.py` | `Estimativa populacional` |
</details>

<details>
<summary>📊 Tabelas do painel GiroSUS (gold)</summary>

Todas em `data/gold/girosus/`. Regras: só AIH regular (IDENT = 1), safra = ano da competência (só a safra 2025), todas as causas de internação.

#### fato_internacoes

| Coluna | Tipo | O que é | Origem / regra | Exemplo |
|---|---|---|---|---|
| `chave_aih` | texto | Número da internação | N_AIH | `5225100458160` |
| `safra` | número | Ano da competência. Filtro principal do painel (2025) | ANO_CMPT | `2025` |
| `competencia` | data | 1º dia do mês da competência | ANO_CMPT + MES_CMPT | `2025-02-01` |
| `data_internacao` | data | Data de entrada | DT_INTER | `2025-01-25` |
| `data_saida` | data | Data de saída | DT_SAIDA | `2025-02-04` |
| `cnes` | texto | Hospital (7 dígitos) | CNES | `0965324` |
| `munic_residencia` | texto | Município onde o paciente mora | MUNIC_RES | `522140` |
| `munic_atendimento` | texto | Município do hospital | MUNIC_MOV | `520870` |
| `cid` | texto | Diagnóstico principal | DIAG_PRINC | `J181` |
| `proc_rea` | texto | Procedimento realizado | PROC_REA | `0303140151` |
| `leito_dias` | número | Dias de internação = leitos-dia | DIAS_PERM | `10` |
| `tempo_tipico` | número | Mediana de dias do mesmo procedimento na mesma safra | mediana(DIAS_PERM) por safra e PROC_REA | `4` |
| `dias_acima_tipico` | número | Dias além do tempo típico (0 se ficou menos) | max(0, leito_dias − tempo_tipico) | `6` |
| `faixa_duracao` | texto | Faixa de duração: 0 dia, 1–3, 4–7, 8–15, 16–30, > 30 | leito_dias | `8–15` |
| `ordem_faixa` | número | Ordem da faixa (1 a 6), só para classificar no Power BI | faixa_duracao | `4` |
| `faixa_pagamento` | texto | Faixa de dias do gráfico de pagamento da pneumonia: 1–2 dias (inclui 0 dia), 3–4 dias, 5–7 dias, 8–14 dias, 15+ dias | leito_dias | `8–14 dias` |
| `ordem_faixa_pagamento` | número | Ordem da faixa de pagamento (1 a 5), só para classificar no Power BI | faixa_pagamento | `4` |
| `fl_permanencia_longa` | número (0/1) | 1 = internação de mais de 15 dias | leito_dias > 15 | `0` |
| `fl_fora_municipio` | número (0/1) | 1 = internado fora do município onde mora | MUNIC_RES ≠ MUNIC_MOV | `1` |
| `fl_uti` | número (0/1) | 1 = passou pela UTI | UTI_MES_TO > 0 | `0` |
| `dias_uti` | número | Dias de UTI | UTI_MES_TO | `0` |
| `valor_pago` | número (R$) | Valor pago pelo SUS (não é o custo real do hospital) | VAL_TOT | `753.34` |
| `valor_uti` | número (R$) | Parte do valor paga pela UTI. Sem os arquivos brutos, o script para com erro | VAL_UTI (`data/raw/sih`) | `0.00` |
| `diarias_acompanhante` | número | Diárias de acompanhante pagas na internação. Sem os arquivos brutos, o script para com erro | DIAR_ACOM (`data/raw/sih`) | `10` |
| `fl_acompanhante` | número (0/1) | 1 = teve diária de acompanhante paga | diarias_acompanhante > 0 | `1` |

#### fato_ocupacao_diaria

| Coluna | Tipo | O que é | Origem / regra | Exemplo |
|---|---|---|---|---|
| `cnes` | texto | Hospital | CNES | `7743068` |
| `data` | data | Dia de 2025 (01/01/2025 a 31/12/2025) | calendário | `2025-05-20` |
| `grupo_doenca` | texto | Grupo de doença (capítulo da CID-10) | DIAG_PRINC | `Respiratório` |
| `pacientes_internados` | número | Pacientes internados no dia: entrou até o dia e saiu depois dele | DT_INTER, DT_SAIDA | `422` |
| `entradas` | número | Internações que começaram no dia | DT_INTER | `94` |
| `altas` | número | Saídas no dia | DT_SAIDA | `88` |

#### dim_tempo

| Coluna | Tipo | O que é | Origem / regra | Exemplo |
|---|---|---|---|---|
| `data` | data | Dia do calendário (17/05/2024 a 31/12/2025). Começa em 2024 só para ligar as AIHs cobradas em 2025 de quem entrou em 2024 | gerado pelo script | `2025-05-20` |
| `ano` | número | Ano da data | data | `2025` |
| `mes` | número | Mês da data (1 a 12) | data | `5` |
| `nome_mes` | texto | Mês abreviado (jan…dez). Classificar por `mes` | data | `mai` |
| `ano_mes` | texto | AAAA-MM | data | `2025-05` |
| `dia_semana` | número | 1 = segunda … 7 = domingo | data | `2` |
| `nome_dia` | texto | seg…dom. Classificar por `dia_semana` | data | `ter` |
| `fl_fim_semana` | número (0/1) | 1 = sábado ou domingo | data | `0` |

#### dim_diagnostico

| Coluna | Tipo | O que é | Origem / regra | Exemplo |
|---|---|---|---|---|
| `cid` | texto | Código CID-10 | DIAG_PRINC | `J189` |
| `capitulo` | texto | 1ª letra do CID | DIAG_PRINC | `J` |
| `grupo_doenca` | texto | Grupo: Lesões e traumas, Respiratório, Circulatório, Infecciosas, Digestivo, Gravidez e parto, Câncer, Saúde mental… | capítulo da CID-10 (D00 a D48 = Câncer; D50 a D89 = Sangue; S e T = Lesões e traumas) | `Respiratório` |

#### dim_procedimento

| Coluna | Tipo | O que é | Origem / regra | Exemplo |
|---|---|---|---|---|
| `proc_rea` | texto | Código do procedimento SIGTAP | PROC_REA | `0303140151` |
| `diagnostico_mais_comum` | texto | CID que mais aparece com esse procedimento | DIAG_PRINC | `J189` |
| `tempo_tipico_2025` | número | Mediana de dias do procedimento na safra 2025 | DIAS_PERM | `4` |
| `nome_procedimento` | texto | 8 nomes definidos no script; os demais `Procedimento <código>` (nenhuma base local tem o nome). Pode trocar à mão pelo nome SIGTAP | script / manual | `Pneumonia ou gripe` |

#### dim_hospital

| Coluna | Tipo | O que é | Origem / regra | Exemplo |
|---|---|---|---|---|
| `cnes` | texto | Código do hospital. O SIH não tem o nome do hospital | coluna CNES do SIH (RD) | `0965324` |
| `municipio_atendimento` | texto | Município do hospital (o mais frequente para aquele CNES) | MUNIC_MOV | `520870` |
| `nome_municipio` | texto | Nome do município | tabela do IBGE | `Goiânia` |

#### dim_municipio_residencia / dim_municipio_atendimento

| Coluna | Tipo | O que é | Origem / regra | Exemplo |
|---|---|---|---|---|
| `codigo` | texto | Código do município (6 dígitos) | MUNIC_RES / MUNIC_MOV | `522140` |
| `nome` | texto | Nome do município | tabela do IBGE | `Trindade` |
| `uf` | texto | Estado | tabela do IBGE | `GO` |
| `fl_goias` | número (0/1) | 1 = município de Goiás (código começa com 52) | codigo | `1` |

#### sazonalidade_mensal

Tabela de apoio, sem relacionamento. Alimenta o mapa de calor da página 17 do `GiroSUS_modelagem_bi.pdf` (sazonalidade). No Power BI: visual Matriz com `grupo_doenca` nas linhas, `nome_mes` nas colunas e `variacao_pct` com formatação condicional. Não some `internados_dia` entre grupos e o total.

| Coluna | Tipo | O que é | Origem / regra | Exemplo |
|---|---|---|---|---|
| `mes` | número | Mês (1 a 12) | data da ocupação diária | `5` |
| `nome_mes` | texto | Mês abreviado. Classificar por `mes` | mes | `mai` |
| `grupo_doenca` | texto | Grupo de doença, ou `Total da rede` | fato_ocupacao_diaria | `Respiratório` |
| `fl_total` | número (0/1) | 1 = linha da rede inteira | grupo_doenca | `0` |
| `internados_dia` | número | Média de pacientes internados por dia no mês (dias sem paciente contam como 0) | pacientes_internados | `818,0` |
| `media_ano` | número | Média de internados por dia no ano, do mesmo grupo | internados_dia | `624,8` |
| `variacao_pct` | número | Quanto o mês fica acima (+) ou abaixo (−) da média do ano do grupo, em % | internados_dia / media_ano − 1 | `30,9` |
| `fl_pico` | número (0/1) | 1 = mês mais cheio do grupo | internados_dia | `1` |
| `fl_vale` | número (0/1) | 1 = mês mais vazio do grupo | internados_dia | `0` |

#### tendencia_anual

Tabela de apoio, sem relacionamento. Mostra se a rede cresce ano a ano (P29). O valor de 2025 é o mesmo "média do ano" do Total da rede na `sazonalidade_mensal` (5.052,8). 2021 fica de fora porque o começo da base não tem quem entrou em 2020.

| Coluna | Tipo | O que é | Origem / regra | Exemplo |
|---|---|---|---|---|
| `ano` | número | Ano (2022 a 2025) | data da ocupação diária | `2025` |
| `internados_dia` | número | Média de pacientes internados por dia no ano (média dos 12 meses), com as AIHs de todas as safras | mesma regra de `pacientes_internados` | `5052,8` |
| `fl_ano_painel` | número (0/1) | 1 = ano da safra do painel (2025) | ano | `1` |
</details>

<details>
<summary>🔢 Códigos: o que significa cada valor</summary>

| Campo | Códigos | Observação |
|---|---|---|
| `IDENT` (SIH) | 1 = AIH regular (internação nova) · 5 = longa permanência (continuação da mesma internação) | 2.235.030 regulares e 51.725 de continuação |
| `MORTE` (SIH) | 0 = não morreu · 1 = óbito na internação | 93.489 óbitos (4,1% dos registros) |
| `CAR_INT` (SIH) | 01 = eletiva (planejada) · 02 = urgência · 05 = outros acidentes de trânsito · 06 = outras lesões e envenenamentos | Quase tudo é 02 (79%) ou 01 (21%) |
| `ESPEC` (SIH) | 01 = cirúrgico · 02 = obstétrico · 03 = clínico · 04 = crônico · 05 = psiquiatria · 06 = pneumologia sanitária (tisiologia) · 07 = pediátrico · 08 = reabilitação · 09 = leito-dia cirúrgico | Os códigos 10, 12, 14, 17 e 87 somam menos de 0,3%: conferir no informe técnico do SIH |
| `SEXO` (SIH) | 1 = masculino · 3 = feminino | Há 2 registros com código 4 (fora do padrão; tratar como ignorado) |
| `COD_IDADE` (SIH) | 2 = dias · 3 = meses · 4 = anos · 5 = 100 anos ou mais (IDADE conta a partir de 100) | Menores de 1 ano vêm em dias ou meses |
| `GESTAO` (SIH) | 1 e 2 = tipo de gestão do hospital (estadual ou municipal) | Conferir no informe técnico do SIH qual é qual antes de usar |
| `TP_LEITO` (CNES) | 1 = cirúrgico · 2 = clínico · 3 = complementar (UTI e UCI) · 4 = obstétrico · 5 = pediátrico · 6 = outras especialidades · 7 = hospital-dia | |
| `TP_UNID` (CNES) | 05 = hospital geral · 07 = hospital especializado · 15 = unidade mista · 20 = pronto-socorro geral · 21 = pronto-socorro especializado · 36 = clínica/centro de especialidade · 61 = centro de parto normal · 62 = hospital-dia · 69 = centro de hemoterapia · 70 = CAPS · 73 = pronto atendimento · 77 = atenção domiciliar | 05 e 07 somam 95% dos registros |
| `CODLEITO` (CNES) | Tipo detalhado do leito. Exemplos: 33 = clínica geral · 75 = UTI adulto tipo II · 78 = UTI pediátrica tipo II · 81 = UTI neonatal tipo II | Lista completa na tabela de tipos de leito do CNES |

Os códigos marcados como “conferir” ainda não foram confirmados na documentação oficial. Na dúvida, confira no informe técnico do DATASUS antes de usar.
</details>

## Notebooks

<details>
<summary>📓 O que cada notebook faz</summary>

Eles seguem uma ordem numerada, e cada um tem um papel:

* **`01`, `02`, `03`:** exploração de cada fonte sozinha (SIH, CNES, IBGE): tamanho, tipos, valores vazios e duplicados.
* **`04`:** primeira versão da consolidação multianual, que hoje o pipeline faz.
* **`05`:** análise integrada, cruzando as três fontes (é anterior ao GiroSUS e não alimenta o painel).
* **`06_girosus_ocupacao_leitos`:** análise do GiroSUS. Calcula, na safra 2025, os números do material do produto e responde as perguntas P1 a P34 do painel em três níveis (o retrato, onde e quem, onde agir), além das curiosidades sobre como o SUS paga uma internação. A sazonalidade (P35 a P40) e a tendência saem do `gerar_modelo_bi_girosus.py`.

Os notebooks de análise (`05` e `06`) leem sempre `data/silver`, nunca os dados brutos. Assim todo mundo analisa a mesma versão conferida.
</details>

<details>
<summary>⚠️ Cuidados: notebooks 01, 02 e 04</summary>

* **Precisam dos `.dbc`:** `01`, `02` e `04` leem os arquivos `.dbc` originais com o PySUS. Como eles não vêm no repositório, esses notebooks param com erro num clone novo. Para rodar, baixe os `.dbc` do DATASUS e coloque em `data/raw/sih/<ano>` e `data/raw/cnes/<ano>`. Os notebooks `03`, `05` e `06` rodam normalmente.
* **O `04` sobrescreve a silver:** a última célula do `04` grava em `data/silver`, mas salva a data de internação (DT_INTER) como texto, enquanto o pipeline salva como data. Não rode essa célula sem necessidade: ela bagunça a silver e faz o teste `test_sih_staging_igual_silver` falhar.
</details>

## Testes

<details>
<summary>✅ O que os testes conferem</summary>

Os testes ficam em `tests/` e rodam com `python -m pytest`. São 15 no total (12 de qualidade da staging e 3 que comparam staging e silver), e eles conferem:

* Colunas importantes sem valores vazios (data de internação, código do município, CNES).
* Nada duplicado nas chaves (por exemplo, município + ano na população).
* Todos os meses do período presentes.
* Códigos de município no formato certo (7 dígitos no IBGE, 6 no SIH).
* Se a staging é igual à silver (`test_staging_silver.py`).
</details>

<details>
<summary>▶️ Como rodar os testes</summary>

Os testes leem `data/staging`, que não vem no repositório. Então, num clone novo, rode o pipeline antes:

```bash
python -m src.pipeline
python -m pytest
```

* Use `python -m pytest`, não só `pytest`. Os testes importam `from src...`, e só o `python -m` coloca a raiz do projeto no caminho do Python. Sem ele, aparece `No module named 'src'`.
* O pipeline mostra na tela cada base gravada (linhas, colunas e tempo). Se não aparecer nada, veja [O comando não mostra nada na tela](#solução-de-problemas).
* Se só os testes de `test_staging_silver.py` falharem, a staging é mais nova que a silver. Rode `python -m src.promover_silver`, que testa e atualiza a silver.
</details>

<details>
<summary>🧪 Como conferir que o projeto inteiro funciona</summary>

Rode na ordem. Cada comando precisa terminar sem nenhuma linha de `ERRO`:

| Comando | O que tem que aparecer |
|---|---|
| `python -m src.converter_dbc` | "Nada a converter" (ou um OK por `.dbc` novo) |
| `python -m src.pipeline` | 3 linhas OK: SIH 2.286.755 linhas e 23 colunas, CNES 198.448 e 12, População 33.422 e 10 |
| `python -m src.orchestration.prefect_flow` | As mesmas 3 linhas OK, no meio dos logs do Prefect, e o flow terminando como `Completed` |
| `python -m src.promover_silver` | 12 passed, 3 arquivos copiados, 3 passed e "Silver atualizada" |
| `python -m pytest` | 15 passed |
| `python gerar_modelo_bi_girosus.py` | Conferência de 2025 batendo (457.403 · 1.835.227 · 726,1 · 43,9), 10 linhas OK e "Todos os 223 numeros conferidos batem" |
| `python testar_estimativa_defasagem.py` | "OK: os 9 números do slide 'Como lidamos com a defasagem' batem" |

Depois, confira à mão:

* `data/gold/girosus/` tem 10 arquivos, todos `.csv`, nenhum `.parquet`.
* O `dim_hospital.csv` abre no Excel com as colunas separadas.
* O notebook `06_girosus_ocupacao_leitos` roda inteiro (Run All) com os mesmos números.
* O `git status` não mostra nada de `data/gold/girosus/` nem de `data/staging/`.
</details>

## Como atualizar os dados

<details>
<summary>📆 Incluir um mês novo do SIH ou do CNES</summary>

1. Baixe o arquivo do mês no [DATASUS](https://datasus.saude.gov.br/transferencia-de-arquivos/): `RDGOAAMM.dbc` para o SIH e `LTGOAAMM.dbc` para o CNES (AA = ano com dois dígitos, MM = mês).
2. Coloque o `.dbc` na pasta do ano (`data/raw/sih/<ano>/` ou `data/raw/cnes/<ano>/`) e converta:
   ```bash
   python -m src.converter_dbc
   ```
   Ele cria o `.parquet` com o mesmo nome, ao lado do `.dbc`, com todas as colunas como texto.
3. Atualize os testes de período (`tests/test_sih.py` e `tests/test_cnes.py`), que conferem quantos meses existem e qual é o último.
4. Rode o pipeline:
   ```bash
   python -m src.pipeline
   ```
5. Promova para a silver. O script roda os testes de qualidade e só copia se passarem; depois confere se staging e silver ficaram iguais:
   ```bash
   python -m src.promover_silver
   ```
6. Gere de novo as tabelas do painel:
   ```bash
   python gerar_modelo_bi_girosus.py
   ```
</details>

<details>
<summary>🗓️ Incluir um ano novo</summary>

Além dos passos acima:

* Ajuste `ANO_FINAL` em `src/config.py`.
* Coloque a planilha de população do ano em `data/raw/ibge/estimativas/<ano>/` e registre o arquivo e o nome da aba em `ARQUIVOS_IBGE`, no `src/extract/ibge.py`.
* Atualize o teste de período da população (`tests/test_populacao.py`).
</details>

## Solução de problemas

<details>
<summary>❌ O ambiente não instala ou dá erro</summary>

1. Apague a pasta `.venv` manualmente.
2. Confira a versão do Python (precisa ser 3.12.x):
   ```bash
   python --version
   ```
3. Refaça o ambiente:
   ```bash
   py -3.12 -m venv .venv
   source .venv/Scripts/activate
   pip install -r requirements.txt
   ```
</details>

<details>
<summary>⏳ O notebook fica carregando e não roda as células no VS Code</summary>

A versão 7 do `ipykernel` tem um problema conhecido com a extensão Jupyter do VS Code que trava as células ([issue #17228](https://github.com/microsoft/vscode-jupyter/issues/17228)). Por isso o `requirements.txt` fixa `ipykernel<7`.

Confira a versão instalada:

```bash
pip show ipykernel
```

Se for 7.x, instale a 6 e recarregue o VS Code (`Ctrl+Shift+P` e depois `Developer: Reload Window`):

```bash
pip install "ipykernel<7"
```
</details>

<details>
<summary>🧩 O VS Code pede para escolher ou instalar um kernel</summary>

Clique no nome do kernel no canto superior direito do notebook, escolha "Select Another Kernel", depois "Python Environments", e selecione o `.venv` do projeto (Python 3.12). Confira também se o `.venv` está ativo e se você rodou `pip install -r requirements.txt`.
</details>

<details>
<summary>🔇 O comando não mostra nada na tela</summary>

No Windows, às vezes o `python` abre o atalho da Microsoft Store, que não faz nada e não mostra erro. Ative o ambiente (`source .venv/Scripts/activate`) ou chame o Python do projeto direto: `.venv/Scripts/python.exe gerar_modelo_bi_girosus.py`. Todos os scripts do projeto mostram mensagens enquanto rodam; se não apareceu nada, o script não rodou.
</details>

<details>
<summary>❌ O pytest dá “No module named 'src'”</summary>

Rode `python -m pytest` em vez de `pytest`, sempre na pasta do projeto. Veja [Como rodar os testes](#testes).
</details>

<details>
<summary>⚠️ Aparecem avisos amarelos (DeprecationWarning)</summary>

Vêm das bibliotecas (`dateutil`, NumPy), não do código do projeto, e não mudam nenhum número. Pode seguir. Só é problema se aparecer `ERRO` ou `FAILED`.
</details>

<details>
<summary>❌ Os testes falham com “arquivo não encontrado”</summary>

Os testes leem `data/staging`, que só existe depois de rodar o pipeline. Rode `python -m src.pipeline` antes do `python -m pytest`.
</details>

<details>
<summary>⛔ O push foi recusado por arquivo grande</summary>

O GitHub recusa arquivos acima de 100 MB (como o CSV da `fato_internacoes`). Se ele entrou num commit, colocar no `.gitignore` depois não basta: o commit antigo continua na fila. Refaça os commits locais sem o arquivo:

```bash
git fetch origin
git reset --soft origin/main
git rm -r --cached data/gold/girosus
git status          # a pasta girosus não pode aparecer em verde
git commit -m "sua mensagem"
git push -u origin nome-da-branch
```

O `reset --soft` não apaga nenhuma alteração, e o `rm --cached` tira o arquivo só do Git, não da sua pasta.
</details>

<details>
<summary>❌ Os notebooks 01, 02 ou 04 dão erro logo no começo</summary>

Eles procuram os arquivos `.dbc`, que não vêm no repositório. Veja [Cuidados: notebooks 01, 02 e 04](#notebooks).
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
3. Não suba `.venv/`, `data/staging/`, `data/gold/girosus/` nem os `.dbc` (já estão no `.gitignore`). Se um push for recusado por arquivo grande, veja [O push foi recusado por arquivo grande](#solução-de-problemas).
4. Envie a branch e abra um pull request para a `main`:
   ```bash
   git push -u origin nome-da-branch
   ```
</details>

<details>
<summary>📓 Cuidados com os notebooks no Git</summary>

Quando você roda um notebook, o VS Code grava os resultados dentro do `.ipynb`, e o Git passa a mostrar o arquivo como modificado. Se você só rodou, sem mudar o código, descarte essas alterações antes de commitar:

```bash
git restore notebooks/
```

Atenção: esse comando desfaz **todas** as alterações não commitadas nos notebooks. Se você editou algum de propósito, restaure só os outros, informando o nome de cada arquivo.
</details>

## Perguntas frequentes

<details>
<summary>🏥 Por que o painel não mostra o nome do hospital? Isso muda algum número?</summary>

**Por que o painel não mostra o nome do hospital, e qual o impacto.** O SIH não traz o nome do hospital: traz o código CNES, que é o identificador oficial de cada estabelecimento no país. Como o GiroSUS usa só o SIH, o hospital aparece como "código · município" (ex.: `7743068 · Goiânia`). Foi uma decisão: uma base oficial só, sem cadastro extra para baixar e manter, e sem risco de ligar um hospital ao nome errado ou de deixar o nome em branco.

* **Impacto nos números: nenhum.** Todos os indicadores por hospital (leitos-dia, dias acima do típico, R$ por dia) são calculados pelo código CNES, e os 260 hospitais da safra 2025 têm código e município.
* **Impacto na leitura:** o gestor vê o código em vez do nome. O diretor conhece o CNES do próprio hospital, e qualquer código pode ser consultado no site público do CNES ([cnes.datasus.gov.br](https://cnes.datasus.gov.br/)).
* **Se o cliente quiser os nomes:** dá para acrescentar depois o cadastro de estabelecimentos do CNES como tabela de apoio, sem mudar nenhum número.
</details>

<details>
<summary>🐍 Qual linguagem e quais bibliotecas o projeto usa</summary>

| Biblioteca | Para quê |
|---|---|
| Python 3.12 | A linguagem do projeto |
| pandas | Manipular as tabelas |
| pyarrow | Ler e gravar Parquet |
| openpyxl e xlrd | Ler as planilhas do IBGE |
| prefect | Organizar (orquestrar) o pipeline |
| pytest | Rodar os testes |
| ipykernel | Rodar os notebooks no VS Code |
| PySUS | Ler e converter os `.dbc` do DATASUS (`src/converter_dbc.py` e notebooks `01`, `02` e `04`) |
</details>

<details>
<summary>🔄 Dá para refazer tudo do zero</summary>

Sim, com uma etapa manual: baixar os `.dbc` no site do DATASUS. Daí em diante são quatro comandos: `python -m src.converter_dbc`, `python -m src.pipeline` (ou `python -m src.orchestration.prefect_flow`, que faz o mesmo organizado com Prefect e roda local, sem servidor), `python -m src.promover_silver` e `python gerar_modelo_bi_girosus.py`.
</details>

## Bases de dados e fontes

<details>
<summary>🏥 SIH/SUS, Internações Hospitalares (AIH) · base do produto</summary>

**O que é:** a base de internações do SUS, com procedimentos, diagnósticos, datas de entrada e saída, município do paciente e do hospital e valores pagos.

**Arquivos usados:** AIH Reduzida (RD).

**Fonte:** [DATASUS, Transferência de Arquivos](https://datasus.saude.gov.br/transferencia-de-arquivos/), com o informe técnico do sistema.
</details>

<details>
<summary>🛏️ CNES, Estabelecimentos e Leitos · exploração, fora do GiroSUS</summary>

**O que é:** o Cadastro Nacional de Estabelecimentos de Saúde: tipos de leito e capacidade instalada de cada estabelecimento. No projeto, foi usado na exploração (notebooks `02` e `05`); não entra no GiroSUS.

**Arquivos usados:** Leitos (LT).

**Fonte:** [DATASUS, Transferência de Arquivos](https://datasus.saude.gov.br/transferencia-de-arquivos/), com o informe técnico do sistema.
</details>

<details>
<summary>👥 IBGE, População Municipal · apoio</summary>

**Para que serve no projeto:** no GiroSUS, só dar nome aos municípios. No notebook `05`, calcular indicadores por habitante, como internações por 10 mil habitantes.

* **Estimativas da População:** estimativas anuais por município. [Acessar](https://ftp.ibge.gov.br/Estimativas_de_Populacao/)
* **Censo Demográfico 2022, População e Domicílios:** [Acessar](https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Populacao_e_domicilios_Primeiros_resultados/)
* **População dos Municípios enviada ao TCU, 2023:** [Acessar](https://ftp.ibge.gov.br/Informacoes_Gerais_e_Referencia/Relacao_da_Populacao_dos_Municipios_para_publicacao_no_DOU_em_2023/)
</details>

<details>
<summary>📚 Tabelas de apoio</summary>

* **Procedimentos e valores:** tabela SIGTAP do SUS.
* **Diagnósticos:** Classificação Internacional de Doenças, 10ª revisão (CID-10).
</details>

## Referências e benchmarks

* **SUS 360º:** estrutura por módulos, KPIs, leitos, capacidade e mapas. [Acessar](https://sus360.saude.gov.br/)
* **ElastiCNES:** mapas, tipos de leitos e filtros geográficos. [Acessar](https://elasticnes.saude.gov.br/)
* **Internações Hospitalares, São Paulo:** dimensões, filtros e perguntas possíveis com dados de internação. [Acessar](https://prefeitura.sp.gov.br/web/saude/tabnet/internacoes_hospitalares)
* **Painel e-SUS APS:** experiência do usuário e organização de informações para gestão em saúde. [Acessar](https://sisaps.saude.gov.br/sistemas/esusaps/)
* **Observatório de Saúde Infantil:** projeto no GitHub com dados do SIM e do SIH sobre mortalidade e internações de crianças de 0 a 6 anos. [Acessar](https://github.com/fmdsocial/sim-sih-mortalidade-internacoes-0-6-anos)
* **SUS Data Analysis:** repositório com análises de dados públicos do SUS. [Acessar](https://github.com/claudioavgo/sus-data-analysis)

## Status do projeto

O que já existe e o que falta. Legenda: ✅ pronto · ❌ falta.

<details>
<summary>🗂️ Dados</summary>

* ✅ **Dados brutos** (`data/raw/`): SIH de jan/2021 a jun/2026 (base do produto); CNES de jan/2021 a jul/2026 e planilhas do IBGE (exploração e apoio). SIH e CNES em Parquet, convertidos do `.dbc` por `src/converter_dbc.py`.
* ✅ **Staging** (`data/staging/`): gerada pelo pipeline, só na sua máquina.
* ✅ **Silver** (`data/silver/`): SIH, CNES e população, conferidas e promovidas por `src/promover_silver.py`.
* ✅ **Tabelas do painel** (`data/gold/girosus/`): 10 tabelas em CSV, geradas pelo script, só na sua máquina.
</details>

<details>
<summary>🐍 Código</summary>

* ✅ **Configuração central** (`src/config.py`): anos, estado e caminhos.
* ✅ **Extração** (`src/extract/`) e **padronização** (`src/transform/`), um módulo por fonte.
* ✅ **Conversão** `.dbc` → `.parquet` (`src/converter_dbc.py`).
* ✅ **Pipeline** (`src/pipeline.py`) e **orquestração com Prefect** (`src/orchestration/`), com mensagens na tela.
* ✅ **Promoção automática** da staging para a silver, com testes antes e depois (`src/promover_silver.py`).
* ✅ **Script do painel** (`gerar_modelo_bi_girosus.py`): aplica as regras do GiroSUS, gera os CSVs e confere o resultado.
* ✅ **Teste da defasagem** (`testar_estimativa_defasagem.py`): mede o atraso da cobrança e testa a estimativa dos meses incompletos e do custo com 2025.
* ✅ **Testes** (`tests/`): 15 testes com pytest.
</details>

<details>
<summary>📓 Análises</summary>

* ✅ **Notebooks 01 a 05**: exploração, consolidação e análise integrada.
* ✅ **Notebook `06_girosus_ocupacao_leitos`**: análise do GiroSUS, com as perguntas P1 a P34. A sazonalidade (P35 a P40) e a tendência saem do `gerar_modelo_bi_girosus.py`.
</details>

<details>
<summary>📖 Documentação</summary>

* ✅ **README** (este arquivo), com o [Dicionário de dados](#dicionário-de-dados).
* ✅ **Dicionário em planilha**: `docs/dicionário/GiroSUS_dicionario_dados.csv`.
* ✅ **PDF do código**: `docs/code/GiroSUS_como_funciona.pdf` (metodologia, pasta por pasta, e a lista dos tratamentos).
* ✅ **PDFs do painel**: `docs/bi/GiroSUS_modelagem_bi.pdf` (negócio: pergunta, gráfico e regra) e `docs/bi/GiroSUS_modelagem_dax.pdf` (medidas DAX).
* ✅ **Pitch**: `docs/apresentacao/GiroSUS_pitch.pdf`.
</details>

<details>
<summary>📊 Produto (Power BI)</summary>

* ✅ **Modelo desenhado**: 2 fatos, 6 dimensões, 2 tabelas de apoio, as medidas DAX e o parâmetro "Redução %" (em `docs/bi/GiroSUS_modelagem_dax.pdf`).
* ❌ **Arquivo `.pbix`** montado.
* ❌ **Painel publicado**, com link, no Power BI Service.
* ✅ **Campos vazios corrigidos** (`dim_hospital` e `dim_procedimento`): `nome_hospital` foi removido (o SIH não traz o nome do hospital) e todo procedimento tem nome ou o rótulo `Procedimento <código>`. O script para com ERRO se qualquer célula vier vazia.
* ✅ **Decisão: só a base SIH.** O painel usa apenas o SIH/SUS, sem bases extras. Por isso o hospital aparece pelo código CNES e pelo município, e os procedimentos têm 8 nomes definidos no script; os demais aparecem como `Procedimento <código>`.
</details>

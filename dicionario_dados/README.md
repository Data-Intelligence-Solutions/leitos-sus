# Dicionário de dados · leitos-sus

Tudo o que cada coluna dos nossos dados significa, de onde vem e um exemplo. Este arquivo é a versão para ler; a mesma informação está em [`dicionario_dados.csv`](dicionario_dados.csv), para abrir no Excel ou filtrar.

## Como ler este dicionário

* **Camada:** `silver` = bases tratadas pelo pipeline (`data/silver`); `gold` = tabelas do painel GiroSUS, geradas por `python gerar_modelo_bi_girosus.py` (`data/gold/girosus`).
* **Tipo:** “texto (número)” quer dizer que o valor é um número, mas vem guardado como texto no arquivo do DATASUS. Converta antes de somar (o script do GiroSUS já faz isso).
* **Origem:** o campo do arquivo original do DATASUS (RD = internações do SIH; LT = leitos do CNES) ou a regra usada para criar a coluna.
* **SEXO, IDADE, COD_IDADE e GESTAO:** já são extraídos pelo pipeline e estão em `data/staging`, mas só aparecem em `data/silver` depois de promover a staging (`cp data/staging/*.parquet data/silver/`).

## Sumário

* [SIH, internações (silver)](#sih-internações-silver)
* [CNES, leitos (silver)](#cnes-leitos-silver)
* [IBGE, população (silver)](#ibge-população-silver)
* [Tabelas do painel GiroSUS (gold)](#tabelas-do-painel-girosus-gold)
* [Códigos: o que significa cada valor](#códigos-o-que-significa-cada-valor)
* [Fontes](#fontes)

## SIH, internações (silver)

Arquivo: `data/silver/sih_multianual.parquet` · 1 linha = 1 AIH (inclui as de continuação) · 2.286.755 registros, competências jan/2021 a jun/2026, hospitais de Goiás.

| Coluna | Tipo | O que é | Origem / regra | Exemplo |
|---|---|---|---|---|
| `ANO_CMPT` | texto | Ano da competência: ano em que o hospital apresentou a AIH para pagamento | SIH (RD) | `2025` |
| `MES_CMPT` | texto | Mês da competência, com 2 dígitos | SIH (RD) | `05` |
| `N_AIH` | texto | Número da AIH (Autorização de Internação Hospitalar). Identifica a internação, não a pessoa | SIH (RD) | `5220103703310` |
| `IDENT` | texto | Tipo da AIH. Ver códigos | SIH (RD) | `1` |
| `SEQ_AIH5` | texto | Sequencial da AIH de longa permanência. Em Goiás vem sempre 000 | SIH (RD) | `000` |
| `CNES` | texto | Código do hospital no Cadastro Nacional de Estabelecimentos de Saúde (7 dígitos) | SIH (RD) | `6665322` |
| `MUNIC_RES` | texto | Município onde o paciente mora (código IBGE de 6 dígitos, sem o dígito verificador) | SIH (RD) | `521930` |
| `MUNIC_MOV` | texto | Município onde fica o hospital (onde a internação aconteceu), 6 dígitos | SIH (RD) | `520870` |
| `DT_INTER` | data | Data de entrada do paciente no hospital | SIH (RD); convertida para data em src/transform/sih.py | `2025-01-25` |
| `DT_SAIDA` | texto | Data de saída (alta, transferência ou óbito), no formato AAAAMMDD | SIH (RD) | `20250204` |
| `DIAS_PERM` | texto (número) | Dias de permanência. É o leito-dia da internação | SIH (RD) | `3` |
| `UTI_MES_TO` | texto (número) | Total de dias em UTI na internação. 0 = não usou UTI | SIH (RD) | `0` |
| `VAL_TOT` | texto (número) | Valor total pago pelo SUS pela internação, em R$. Não é o custo real do hospital | SIH (RD) | `485.78` |
| `DIAG_PRINC` | texto | Diagnóstico principal pela CID-10. A 1ª letra indica o capítulo (J = respiratório, I = circulatório…) | SIH (RD) | `J189` |
| `MORTE` | texto | Indica se o paciente morreu na internação. Ver códigos | SIH (RD) | `0` |
| `ESPEC` | texto | Especialidade do leito em que o paciente ficou. Ver códigos | SIH (RD) | `03` |
| `PROC_REA` | texto | Procedimento realizado, pela tabela SIGTAP (10 dígitos). Define o valor pago | SIH (RD) | `0303140151` |
| `CAR_INT` | texto | Caráter da internação (eletiva, urgência, acidente). Ver códigos | SIH (RD) | `02` |
| `SEXO` | texto | Sexo do paciente. Ver códigos | SIH (RD) · entra na silver ao promover a staging atual | `3` |
| `IDADE` | texto (número) | Idade do paciente, na unidade indicada por COD_IDADE | SIH (RD) · entra na silver ao promover a staging atual | `27` |
| `COD_IDADE` | texto | Unidade da idade (dias, meses, anos). Ver códigos | SIH (RD) · entra na silver ao promover a staging atual | `4` |
| `GESTAO` | texto | Tipo de gestão do hospital. Ver códigos | SIH (RD) · entra na silver ao promover a staging atual | `1` |
| `ARQUIVO_ORIGEM` | texto | Nome do arquivo mensal do DATASUS de onde veio a linha (RDGO + AAMM) | Criada em src/extract/sih.py | `RDGO2505.dbc` |

## CNES, leitos (silver)

Arquivo: `data/silver/cnes_multianual.parquet` · 1 linha = 1 tipo de leito de 1 estabelecimento em 1 mês · 198.448 registros, jan/2021 a jul/2026.

| Coluna | Tipo | O que é | Origem / regra | Exemplo |
|---|---|---|---|---|
| `CNES` | texto | Código do estabelecimento de saúde (7 dígitos) | CNES (LT) | `9331603` |
| `CODUFMUN` | texto | Município do estabelecimento (código IBGE de 6 dígitos) | CNES (LT) | `520010` |
| `TP_UNID` | texto | Tipo de unidade (hospital geral, especializado, unidade mista…). Ver códigos | CNES (LT) | `05` |
| `TP_LEITO` | texto | Grande tipo de leito (cirúrgico, clínico, complementar/UTI…). Ver códigos | CNES (LT) | `2` |
| `CODLEITO` | texto | Tipo detalhado do leito (ex.: 33 clínica geral, 75 UTI adulto tipo II) | CNES (LT) | `33` |
| `QT_EXIST` | número | Quantidade de leitos existentes daquele tipo | CNES (LT); convertida para número em src/transform/cnes.py | `9` |
| `QT_SUS` | número | Quantidade desses leitos disponíveis para o SUS | CNES (LT); convertida para número | `9` |
| `QT_NSUS` | número | Quantidade de leitos não SUS (planos e particulares) | CNES (LT); convertida para número | `0` |
| `COMPETEN` | texto | Competência (mês de referência) no formato AAAAMM | CNES (LT) | `202101` |
| `ARQUIVO_ORIGEM` | texto | Arquivo mensal de origem (LTGO + AAMM) | Criada em src/extract/cnes.py | `LTGO2101.dbc` |
| `ANO` | número | Ano da competência, tirado do nome do arquivo | Criada em src/transform/cnes.py | `2021` |
| `MES` | número | Mês da competência, tirado do nome do arquivo | Criada em src/transform/cnes.py | `1` |

## IBGE, população (silver)

Arquivo: `data/silver/populacao_multianual.parquet` · 1 linha = 1 município em 1 ano · 33.422 registros, todos os municípios do Brasil, 2021 a 2026.

| Coluna | Tipo | O que é | Origem / regra | Exemplo |
|---|---|---|---|---|
| `uf` | texto | Sigla do estado | IBGE | `GO` |
| `cod_uf` | texto | Código do estado (2 dígitos). Goiás = 52 | IBGE | `52` |
| `cod_municipio` | texto | Parte do código do município dentro do estado (5 dígitos) | IBGE | `08707` |
| `municipio` | texto | Nome do município | IBGE | `Goiânia` |
| `populacao` | número inteiro | População do município no ano de referência | IBGE; limpa em src/transform/populacao.py | `1503256` |
| `codigo_ibge_7` | texto | Código IBGE completo (7 dígitos). Os 6 primeiros batem com os códigos do SIH e do CNES | cod_uf + cod_municipio | `5208707` |
| `ano_referencia` | número | Ano a que a população se refere (2021 a 2026) | Criada em src/transform/populacao.py | `2025` |
| `ano_publicacao` | número | Ano em que o IBGE publicou o dado. Vazio em 2023 (valor calculado pelo projeto) | Criada em src/transform/populacao.py | `2025` |
| `origem` | texto | IBGE ou “Cálculo próprio com dados IBGE” (2023) | Criada em src/transform/populacao.py | `IBGE` |
| `tipo_dado` | texto | Tipo da fonte: estimativa anual, Censo 2022 (TCU) ou interpolação 2022–2024 | Criada em src/transform/populacao.py | `Estimativa populacional` |

## Tabelas do painel GiroSUS (gold)

Geradas por `python gerar_modelo_bi_girosus.py` em `data/gold/girosus/`. Regras: só AIH regular (IDENT = 1), safra = ano da competência (padrão do painel: 2025), todas as causas de internação.

### fato_internacoes

Arquivo: `data/gold/girosus/fato_internacoes.parquet`

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
| `faixa_duracao` | texto | Faixa de duração: 0 dia, 1–3, 4–7, 8–15, 16–30, > 30 | a partir de leito_dias | `8–15` |
| `ordem_faixa` | número | Ordem da faixa (1 a 6), só para classificar no Power BI | a partir de faixa_duracao | `4` |
| `fl_fora_municipio` | número (0/1) | 1 = internado fora do município onde mora | MUNIC_RES ≠ MUNIC_MOV | `1` |
| `fl_uti` | número (0/1) | 1 = passou pela UTI | UTI_MES_TO > 0 | `0` |
| `dias_uti` | número | Dias de UTI | UTI_MES_TO | `0` |
| `valor_pago` | número (R$) | Valor pago pelo SUS | VAL_TOT | `753.34` |
| `valor_uti` | número (R$) | Parte do valor paga pela UTI. Vazio se os arquivos brutos não estiverem na máquina | VAL_UTI (data/raw/sih) | `0.00` |

### fato_ocupacao_diaria

Arquivo: `data/gold/girosus/fato_ocupacao_diaria.parquet`

| Coluna | Tipo | O que é | Origem / regra | Exemplo |
|---|---|---|---|---|
| `cnes` | texto | Hospital | CNES | `7743068` |
| `data` | data | Dia (01/01/2021 a 30/06/2026) | calendário | `2025-05-20` |
| `grupo_doenca` | texto | Grupo de doença (capítulo da CID-10) | DIAG_PRINC | `Respiratório` |
| `pacientes_internados` | número | Pacientes internados no dia: entrada ≤ dia e saída > dia | DT_INTER, DT_SAIDA | `422` |
| `entradas` | número | Internações que começaram no dia | DT_INTER | `94` |
| `altas` | número | Saídas no dia | DT_SAIDA | `88` |

### dim_tempo

Arquivo: `data/gold/girosus/dim_tempo.parquet`

| Coluna | Tipo | O que é | Origem / regra | Exemplo |
|---|---|---|---|---|
| `data` | data | Dia do calendário (2020 a 2026) | gerado pelo script | `2025-05-20` |
| `ano / mes / trimestre` | número | Ano, mês e trimestre da data | data | `2025 / 5 / 2` |
| `nome_mes` | texto | Mês abreviado (jan…dez). Classificar por mes | data | `mai` |
| `ano_mes` | texto | AAAA-MM | data | `2025-05` |
| `dia_semana` | número | 1 = segunda … 7 = domingo | data | `2` |
| `nome_dia` | texto | seg…dom. Classificar por dia_semana | data | `ter` |
| `fl_fim_semana` | número (0/1) | 1 = sábado ou domingo | data | `0` |

### dim_diagnostico

Arquivo: `data/gold/girosus/dim_diagnostico.parquet`

| Coluna | Tipo | O que é | Origem / regra | Exemplo |
|---|---|---|---|---|
| `cid` | texto | Código CID-10 | DIAG_PRINC | `J189` |
| `capitulo` | texto | 1ª letra do CID | DIAG_PRINC | `J` |
| `grupo_doenca` | texto | Grupo: Lesões e traumas, Respiratório, Circulatório, Infecciosas, Digestivo, Gravidez e parto, Câncer, Saúde mental… | capítulo da CID-10 (D00–D48 = Câncer; D50–D89 = Sangue; S e T = Lesões e traumas) | `Respiratório` |

### dim_procedimento

Arquivo: `data/gold/girosus/dim_procedimento.parquet`

| Coluna | Tipo | O que é | Origem / regra | Exemplo |
|---|---|---|---|---|
| `proc_rea` | texto | Código do procedimento SIGTAP | PROC_REA | `0303140151` |
| `diagnostico_mais_comum` | texto | CID que mais aparece com esse procedimento | DIAG_PRINC | `J189` |
| `tempo_tipico_2025` | número | Mediana de dias do procedimento na safra 2025 | DIAS_PERM | `4` |
| `nome_procedimento` | texto | Nome oficial. Vem em branco: preencher pela tabela SIGTAP | manual | `Tratamento de pneumonias ou influenza (gripe)` |

### dim_hospital

Arquivo: `data/gold/girosus/dim_hospital.parquet`

| Coluna | Tipo | O que é | Origem / regra | Exemplo |
|---|---|---|---|---|
| `cnes` | texto | Código do hospital | CNES | `0965324` |
| `municipio_atendimento` | texto | Município do hospital (o mais frequente para o CNES) | MUNIC_MOV | `520870` |
| `nome_municipio` | texto | Nome do município | tabela do IBGE | `Goiânia` |
| `nome_hospital` | texto | Nome do hospital. Vem em branco: preencher pela consulta pública do CNES | manual | — |

### dim_municipio_residencia / dim_municipio_atendimento

Arquivo: `data/gold/girosus/dim_municipio_*.parquet`

| Coluna | Tipo | O que é | Origem / regra | Exemplo |
|---|---|---|---|---|
| `codigo` | texto | Código do município (6 dígitos) | MUNIC_RES / MUNIC_MOV | `522140` |
| `nome` | texto | Nome do município | tabela do IBGE | `Trindade` |
| `uf` | texto | Estado | tabela do IBGE | `GO` |
| `fl_goias` | número (0/1) | 1 = município de Goiás (código começa com 52) | codigo | `1` |

## Códigos: o que significa cada valor

| Campo | Códigos | Observação |
|---|---|---|
| `IDENT (SIH)` | 1 = AIH regular (internação nova) · 5 = AIH de longa permanência (continuação da mesma internação) | 2.235.030 × 51.725 registros |
| `MORTE (SIH)` | 0 = não morreu · 1 = óbito na internação | 93.489 óbitos (4,1% dos registros) |
| `CAR_INT (SIH)` | 01 = eletiva (planejada) · 02 = urgência · 05 = outros acidentes de trânsito · 06 = outras lesões e envenenamentos | Quase tudo é 02 (79%) ou 01 (21%) |
| `ESPEC (SIH)` | 01 = cirúrgico · 02 = obstétrico · 03 = clínico · 04 = crônico · 05 = psiquiatria · 06 = pneumologia sanitária (tisiologia) · 07 = pediátrico · 08 = reabilitação · 09 = leito-dia cirúrgico | Os códigos 10, 12, 14, 17 e 87 somam menos de 0,3% dos registros: conferir no informe técnico do SIH |
| `SEXO (SIH)` | 1 = masculino · 3 = feminino | Há 2 registros com código 4 (valor fora do padrão; tratar como ignorado) |
| `COD_IDADE (SIH)` | 2 = dias · 3 = meses · 4 = anos · 5 = 100 anos ou mais (IDADE conta a partir de 100) | Menores de 1 ano vêm em dias ou meses |
| `GESTAO (SIH)` | 1 e 2 = tipo de gestão do hospital (estadual ou municipal) | Conferir no informe técnico do SIH qual código é qual antes de usar |
| `TP_LEITO (CNES)` | 1 = cirúrgico · 2 = clínico · 3 = complementar (UTI e UCI) · 4 = obstétrico · 5 = pediátrico · 6 = outras especialidades · 7 = hospital-dia |  |
| `TP_UNID (CNES)` | 05 = hospital geral · 07 = hospital especializado · 15 = unidade mista · 20 = pronto-socorro geral · 21 = pronto-socorro especializado · 36 = clínica/centro de especialidade · 61 = centro de parto normal · 62 = hospital-dia · 69 = centro de hemoterapia · 70 = CAPS · 73 = pronto atendimento · 77 = atenção domiciliar | 05 e 07 somam 95% dos registros |
| `CODLEITO (CNES)` | Tipo detalhado do leito. Exemplos: 33 = clínica geral · 75 = UTI adulto tipo II · 78 = UTI pediátrica tipo II · 81 = UTI neonatal tipo II | Lista completa na tabela de tipos de leito do CNES |

## Fontes

* SIH/SUS e CNES: [DATASUS, Transferência de Arquivos](https://datasus.saude.gov.br/transferencia-de-arquivos/), com a documentação (informe técnico) de cada sistema.
* Procedimentos e valores: tabela SIGTAP do SUS.
* Diagnósticos: Classificação Internacional de Doenças, 10ª revisão (CID-10).
* População: IBGE (estimativas anuais e Censo 2022).

Quando um código não estiver aqui ou houver dúvida, confira no informe técnico do DATASUS antes de usar. Os códigos marcados como “conferir” não foram confirmados na documentação oficial.

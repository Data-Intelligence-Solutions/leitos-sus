# Referências, Benchmarks e Datasets

## Configurar projeto e instalar dependências

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

## 📁 Estrutura do projeto

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

## Principais benchmarks

- **SUS 360º**  
  Estrutura por módulos, KPIs, leitos, capacidade e mapas.  
  [Acessar SUS 360º](https://sus360.saude.gov.br/)

- **ElastiCNES**  
  Referência para mapas, tipos de leitos e filtros geográficos.  
  [Acessar ElastiCNES](https://elasticnes.saude.gov.br/)

- **Internações Hospitalares - São Paulo**  
  Referência para dimensões, filtros e perguntas possíveis utilizando dados de internações hospitalares.  
  [Acessar Internações Hospitalares](https://prefeitura.sp.gov.br/web/saude/tabnet/internacoes_hospitalares)

- **Painel e-SUS APS**  
  Referência de experiência do usuário (UX) e organização de informações para gestão em saúde.  
  [Acessar e-SUS APS](https://sisaps.saude.gov.br/sistemas/esusaps/)

- **Observatório de Saúde Infantil**  
  Projeto no GitHub que utiliza dados do SIM e SIH para análise de mortalidade e internações de crianças de 0 a 6 anos.  
  [Acessar repositório](https://github.com/fmdsocial/sim-sih-mortalidade-internacoes-0-6-anos)

- **SUS Data Analysis**  
  Repositório com análises utilizando dados públicos do SUS.  
  [Acessar repositório](https://github.com/claudioavgo/sus-data-analysis)

---

## Datasets

### SIH/SUS - Internações Hospitalares (AIH)

**O que é:**  
Base de dados de internações hospitalares do SUS contendo informações como procedimentos, diagnósticos, datas de internação e saída, município de residência, município de atendimento e valores registrados nas AIHs.

**Fonte:**  
[DATASUS - Transferência de Arquivos](https://datasus.saude.gov.br/transferencia-de-arquivos/)

**Base utilizada:** SIH/SUS - arquivos de AIH Reduzida (RD).

---

### CNES - Estabelecimentos e Leitos

**O que é:**  
Cadastro Nacional de Estabelecimentos de Saúde, utilizado para obter informações sobre estabelecimentos, tipos de leitos e capacidade hospitalar instalada.

**Fonte:**  
[DATASUS - Transferência de Arquivos](https://datasus.saude.gov.br/transferencia-de-arquivos/)

**Base utilizada:** CNES - arquivos de Leitos (LT).

---

### IBGE - População Municipal

**Uso no projeto:**  
Os dados populacionais são utilizados como referência para contextualização e normalização de indicadores, como internações por 10 mil habitantes.

#### Estimativas da População

Estimativas anuais da população dos municípios brasileiros.

[Acessar Estimativas da População](https://ftp.ibge.gov.br/Estimativas_de_Populacao/)

#### Censo Demográfico 2022 - População e Domicílios

Resultados do Censo Demográfico 2022 relacionados à população e aos domicílios.

[Acessar Censo Demográfico 2022](https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Populacao_e_domicilios_Primeiros_resultados/)

#### População dos Municípios enviada ao TCU - 2023

Arquivos publicados pelo IBGE para divulgação da população dos municípios ao Tribunal de Contas da União (TCU).

[Acessar arquivos do TCU](https://ftp.ibge.gov.br/Informacoes_Gerais_e_Referencia/Relacao_da_Populacao_dos_Municipios_para_publicacao_no_DOU_em_2023/)
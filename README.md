# Taxi ETL

Aplicação Streamlit baseada em análise do dataset Yellow Taxi Trip Records de março de 2016. Fornece dashboards interativos com KPIs, resumos por hora, dia da semana, fornecedor e forma de pagamento.

## Pré-requisitos

- Python 3.10 ou superior
- UV (gerenciador de pacotes) - [Instalar UV](https://docs.astral.sh/uv/getting-started/installation/)
- Conta no Kaggle (para download do dataset)

## Guia de Execução Completo

### 1. Preparar o Ambiente

Clone ou acesse o diretório do projeto:

```bash
cd taxi_ETL
```

### 2. Instalar Dependências com UV

```bash
uv sync
```

Este comando instalará todas as dependências listadas no `pyproject.toml`.

### 3. Preparar o Dataset

#### Opção A: Download Manual (Recomendado)

1. Acesse o dataset no Kaggle: [NYC Yellow Taxi Trip Data](https://www.kaggle.com/datasets/elemento/nyc-yellow-taxi-trip-data?select=yellow_tripdata_2016-03.csv)
2. Faça login ou crie uma conta no Kaggle
3. Clique em "Download" para baixar `yellow_tripdata_2016-03.csv`
4. Extraia o arquivo e coloque-o na pasta `data/`:

```bash
# Estrutura esperada
data/
  └─ yellow_tripdata_2016-03.csv
```

#### Opção B: Download via CLI do Kaggle

Se você tem a CLI do Kaggle configurada:

```bash
kaggle datasets download -d elemento/nyc-yellow-taxi-trip-data
unzip nyc-yellow-taxi-trip-data.zip -d data/
```

### 4. Executar o Notebook (ETL)

O notebook processa o dataset CSV e gera um arquivo Parquet otimizado:

```bash
uv run jupyter notebook notebooks/main.ipynb
```

Ou, se preferir usar o Jupyter integrado ao VS Code, abra `notebooks/main.ipynb` e execute todas as células.

**O que acontece:**
- O notebook lê o CSV em `data/yellow_tripdata_2016-03.csv`
- Processa e transforma os dados
- Salva o resultado em `data/output/yellow_tripdata_2016-03.parquet`

### 5. Executar o Dashboard

Com o ambiente UV ativado, execute:

```bash
uv run streamlit run dashboard.py
```

O dashboard abrirá automaticamente em `http://localhost:8501`

**Nota:** O dashboard carrega automaticamente o arquivo Parquet gerado. Se ele não existir, tentará processar o CSV bruto.

## Filtros Disponíveis

- **Dias da semana**: Filtrar por dias específicos
- **Forma de pagamento**: Cartão, dinheiro, etc.
- **Fornecedores**: Diferentes prestadores de serviço

## Painéis do Dashboard

- **Visão geral com KPIs**: Métricas principais da operação
- **Resumo por hora do dia**: Distribuição de corridas por hora
- **Resumo por dia da semana**: Padrões de uso semanal
- **Resumo por fornecedor**: Comparação entre fornecedores
- **Resumo por forma de pagamento**: Análise de métodos de pagamento

## Troubleshooting

### Problema: "ModuleNotFoundError"
- Verifique se o comando `uv sync` foi executado com sucesso
- Tente executar novamente: `uv sync --upgrade`

### Problema: Arquivo Parquet não encontrado
- Execute o notebook primeiro com `uv run jupyter notebook notebooks/main.ipynb`
- Ou coloque o CSV em `data/` e o dashboard tentará processar automaticamente

### Problema: Porta 8501 já em uso
- Especifique uma porta diferente: `uv run streamlit run dashboard.py --server.port 8502`

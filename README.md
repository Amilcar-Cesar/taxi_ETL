# Taxi ETL

Aplicação Streamlit baseada no notebook de análise do dataset Yellow Taxi Trip Records de março de 2016.

Faça o download do dataset e coloque o arquivo dentro da pasta "data": https://www.kaggle.com/datasets/elemento/nyc-yellow-taxi-trip-data?select=yellow_tripdata_2016-03.csv

O app carrega o parquet gerado pelo notebook em `data/output/yellow_tripdata_2016-03.parquet`. Se ele não existir, o arquivo CSV bruto em `data/yellow_tripdata_2016-03.csv` é processado e o parquet é recriado.

## Executar o dashboard

```bash
streamlit run dashboard.py
```

## Filtros disponíveis

- Dias da semana
- Forma de pagamento
- Fornecedores

## Painéis

- Visão geral com KPIs
- Resumo por hora do dia
- Resumo por dia da semana
- Resumo por fornecedor
- Resumo por forma de pagamento

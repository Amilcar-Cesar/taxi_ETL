# Taxi ETL

Aplicação Streamlit baseada no notebook de análise do dataset Yellow Taxi Trip Records de março de 2016.

## Executar o dashboard

```bash
streamlit run dashboard.py
```

O app carrega o parquet gerado pelo notebook em `data/output/yellow_tripdata_2016-03.parquet`. Se ele não existir, o arquivo CSV bruto em `data/yellow_tripdata_2016-03.csv` é processado e o parquet é recriado.

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

# F1 Analytics

Este projeto tem como objetivo realizar análises exploratórias e visualizações de dados utilizando informações históricas da Fórmula 1.

## Estrutura do Projeto

- `data/raw/`: Dados brutos baixados do Kaggle.
- `data/processed/`: Dados processados para análise.
- `notebooks/`: Notebooks Jupyter para exploração e visualização dos dados.
- `src/data_processing/`: Scripts para download, processamento e preparação dos dados.
- `src/data_viz/`: Scripts para visualização dos dados.

## Como começar

1. Instale as dependências:
   ```sh
   pip install -r requirements.txt
2. Baixe o dataset da F1:

``python src/data_processing/kaggle_download.py``

3. Crie o banco de dados:

``python src/data_processing/create_raw_db.py``

# Análises em andamento...
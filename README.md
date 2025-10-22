# F1 Analytics

Projeto para explorar, consolidar e visualizar dados historicos da Formula 1 usando Python, SQLite e Jupyter Notebooks.

## Visao geral do fluxo

1. **Download dos dados** - `src/data_processing/kaggle_download.py` usa `kagglehub` para copiar os arquivos CSV do Kaggle para `data/raw/`.
2. **Criacao do banco** - `src/data_processing/create_db.py` carrega os CSVs em um banco SQLite localizado em `data/processed/f1.db`.
3. **Consultas e analises** - SQLs em `data/db_queries/` e utilitarios Python (`src/modules/db_reader.py`, `notebooks/utils.py`, `src/data_viz/plotter.py`) suportam notebooks exploratorios e geracao de graficos.

## Pre-requisitos

- Python 3.12+
- Conta no Kaggle com token configurado para uso via `kagglehub` (coloque o arquivo `kaggle.json` no diretorio padrao ou defina as variaveis `KAGGLE_USERNAME` e `KAGGLE_KEY`).
- (Opcional) Ambiente virtual para isolar dependencias.

## Configuracao rapida

```bash
# 1) Criar e ativar um ambiente virtual (opcional)
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1

# 2) Instalar dependencias
pip install -r requirements.txt

# 3) Fazer download e preparar os dados
python src/data_processing/kaggle_download.py
python src/data_processing/create_db.py
```

Apos esses passos, o banco `data/processed/f1.db` estara pronto para uso nas consultas e notebooks.

## Ferramentas do projeto

- `src/modules/db_reader.py`: classe `DbReader` para executar queries SQL retornando `pandas.DataFrame`.
- `data/db_queries/*.sql`: consultas prontas (resultados de corridas, classificatorias, tempos de volta etc.) para alimentar analises.
- `notebooks/utils.py`: funcoes auxiliares para analise temporal, filtros por piloto/circuito e geracao de graficos especificos.
- `src/data_viz/plotter.py`: classe `Plotter` com atalhos para graficos recorrentes em analises exploratorias.

### Exemplo rapido de uso do `DbReader`

```python
from src.modules.db_reader import DbReader

reader = DbReader()  # usa data/processed/f1.db por padrao
df_results = reader.run_query_file("data/db_queries/race_results_report.sql")
print(df_results.head())
```

## Estrutura de pastas

- `data/raw/` - CSVs originais baixados do Kaggle.
- `data/processed/` - artefatos prontos para consumo (SQLite, vistas, relatorios).
- `data/db_queries/` - consultas SQL reutilizaveis.
- `notebooks/` - analises exploratorias (`explore_data.ipynb`, `analise_verstappen.ipynb` etc.).
- `src/data_processing/` - scripts de ingestao e preparacao.
- `src/data_viz/` - utilitarios para visualizacao.
- `src/modules/` - componentes reutilizaveis (ex.: `DbReader`).

## Notebooks em destaque

- `notebooks/explore_data.ipynb` - exploracao inicial das tabelas consolidadas.
- `notebooks/analise_verstappen.ipynb` - estudo focado no desempenho de Max Verstappen (usa funcoes de `notebooks/utils.py`).

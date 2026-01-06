# F1 Analytics

Projeto para explorar, consolidar e visualizar dados historicos da Formula 1 usando Python, SQLite e Jupyter Notebooks.
Feito por João Marcolin com um tanto de vibe-coding com bom senso.

## Visao geral do fluxo

1.  **Download dos dados (Manual)** - Os dados completos (1950-2025+) são baixados manualmente do *dump* do banco de dados Jolpica e colocados em `data/raw/`.
2.  **Criacao do banco** - `src/data_processing/create_db.py` carrega os CSVs do *dump* em um banco SQLite localizado em `data/processed/f1.db`.
3.  **Consultas e analises** - SQLs em `data/db_queries/` e utilitarios Python (`src/modules/data_processing/db_reader.py`, `src/analysis/data_viz/plotter.py` etc) suportam notebooks exploratorios e geracao de graficos.

**NOTA SOBRE DADOS ANTIGOS:** O método anterior de download via `src/data_processing/kaggle_download.py` (usando `kagglehub`) é agora considerado **obsoleto**. Ele ainda funciona, mas os dados do Kaggle param em 2024 e não são mais a fonte principal deste projeto.

## Pré-requisitos

-   Python 3.12+
-   (Opcional) Ambiente virtual para isolar dependencias.

## Configuracao rapida

```bash
# 1. Criar e ativar um ambiente virtual (opcional, mas recomendado)
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# No Linux/macOS, use: source .venv/bin/activate

# 2. Instalar dependências
pip install -r requirements.txt
````

**3) Fazer download e preparar os dados (Processo Manual)**

Como o download automático (`download_data.py`) pode ser instável, o método recomendado é o manual:

1.  **Baixe o .zip:** No seu navegador, acesse a URL do *dump* de dados do Jolpica:
    `https://api.jolpi.ca/data/dumps/download/delayed/?dump_type=csv`
2.  **Mova e Descompacte:** Mova o arquivo `.zip` baixado para a pasta `data/raw/` do projeto e descompacte-o lá.
3.  **Limpe (Opcional):** Você pode apagar o arquivo `.zip` após a extração.

**4) Criar o Banco de Dados**

Após os arquivos CSV estarem em `data/raw/`, execute o script de criação do banco:

```bash
python src/data_processing/create_db.py
```

Apos esses passos, o banco `data/processed/f1.db` estara pronto para uso nas consultas e notebooks.

## Ferramentas do projeto

  - `src/modules/db_reader.py`: classe `DbReader` para executar queries SQL retornando `pandas.DataFrame`.
  - `data/db_queries/*.sql`: consultas prontas (resultados de corridas, classificatorias, tempos de volta etc.) para alimentar analises.
  - `notebooks/utils.py`: funcoes auxiliares para analise temporal, filtros por piloto/circuito e geracao de graficos especificos.
  - `src/data_viz/plotter.py`: classe `Plotter` com atalhos para graficos recorrentes em analises exploratorias.
  - `src/features/` - componentes reutilizaveis para criação de features e variáveis utilizadas em análises.
    - Aqui a lógica é de Domain-Driven Design (DDD). Separo em famílias de features e cada uma recebe seus datasets e lógicas específicas.

### Exemplo rapido de uso do `DbReader`

```python
from src.modules.db_reader import DbReader

reader = DbReader()  # usa data/processed/f1.db por padrao
df_results = reader.run_query_file("data/db_queries/race_results_report.sql")
print(df_results.head())
```

## Estrutura de pastas

  - `data/raw/` - CSVs originais baixados do *dump* do Jolpica.
  - `data/processed/` - artefatos prontos para consumo (SQLite, vistas, relatorios).
  - `data/db_queries/` - consultas SQL reutilizaveis.
  - `notebooks/` - analises exploratorias (`explore_data.ipynb`, `analise_verstappen.ipynb` etc.).
  - `src/data_processing/` - scripts de ingestao e preparacao.
  - `src/data_viz/` - utilitarios para visualizacao.
  - `src/modules/` - componentes reutilizaveis (ex.: `DbReader`).

## Notebooks em destaque

  - `notebooks/explore_data.ipynb` - exploracao inicial das tabelas consolidadas.
  - `notebooks/analise_verstappen.ipynb` - estudo focado no desempenho de Max Verstappen (usa funcoes de `notebooks/utils.py`).
  - `notebooks/2025_championship` - estudo focado em uma retrospectiva e análise do campeonato de 2025.

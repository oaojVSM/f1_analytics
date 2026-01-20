# F1 Analytics

[🇧🇷 Leia em Português (Read in Portuguese)](README.md)

Project to explore, consolidate, and visualize historical Formula 1 data using Python, SQLite, and Jupyter Notebooks.
Made by João Marcolin (with some little assistance from AI).

## Workflow Overview

1.  **Data Download (Manual)** - Full data (1950-2025+) is manually downloaded from the Jolpica database *dump* and placed in `data/raw/`.
2.  **Database Creation** - `src/data_processing/create_db.py` loads the *dump* CSVs into a SQLite database located at `data/processed/f1.db`.
3.  **Queries and Analysis** - SQLs in `data/db_queries/` and Python utilities (`src/modules/data_processing/db_reader.py`, `src/analysis/data_viz/plotter.py` etc) support exploratory notebooks and chart generation.

**NOTE ABOUT OLD DATA:** The previous download method via `src/data_processing/kaggle_download.py` (using `kagglehub`) is now considered **obsolete**. It still works, but Kaggle data stops at 2024 and is no longer the main source for this project.

## Prerequisites

-   Python 3.12+
-   (Optional) Virtual environment to isolate dependencies.

## Quick Setup

```bash
# 1. Create and activate a virtual environment (optional, but recommended)
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# On Linux/macOS, use: source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
````

**3) Download and prepare data (Manual Process)**

As the automatic download (`download_data.py`) can be unstable, the manual method is recommended:

1.  **Download .zip:** In your browser, access the Jolpica data *dump* URL:
    `https://api.jolpi.ca/data/dumps/download/delayed/?dump_type=csv`
2.  **Move and Unzip:** Move the downloaded `.zip` file to the project's `data/raw/` folder and unzip it there.
3.  **Clean (Optional):** You can delete the `.zip` file after extraction.

**4) Create the Database**

After the CSV files are in `data/raw/`, run the database creation script:

```bash
python src/data_processing/create_db.py
```

After these steps, the `data/processed/f1.db` database will be ready for use in queries and notebooks.

### 5) Generate Feature Store (Feature Pipeline)

To feed ML models and advanced analyses, the project has a pipeline that processes raw data and creates consolidated feature tables (e.g., race pace, reliability, performance).

To generate the features, run:

```bash
python src/data_processing/feature_pipeline.py
```

This will create the following files in `data/features/`:
- `pace_features.csv`: Race pace metrics (consistency, teammate comparison, qualifying pace).
- `performance_features.csv`: Result metrics (points, positions gained, qualifying duels).
- `reliability_features.csv`: Failure rates (DNF) and mechanical failures.
- `experience_features.csv`: Driver experience metrics (number of races, podiums, pole positions, etc.).

## Project Tools

  - `src/modules/db_reader.py`: `DbReader` class to execute SQL queries returning `pandas.DataFrame`.
  - `data/db_queries/*.sql`: Ready-made queries (race results, qualifying, lap times, etc.) to feed analyses.
  - `notebooks/utils.py`: Helper functions for temporal analysis, driver/circuit filters, and specific chart generation.
  - `src/data_viz/plotter.py`: `Plotter` class with shortcuts for recurrent charts in exploratory analyses.
  - `src/features/` - Reusable components for feature creation and variables used in analyses.
    - Here the logic is Domain-Driven Design (DDD). I separate into feature families and each receives its specific datasets and logic.

### Quick usage example of `DbReader`

```python
from src.modules.db_reader import DbReader

reader = DbReader()  # uses data/processed/f1.db by default
df_results = reader.run_query_file("data/db_queries/race_results_report.sql")
print(df_results.head())
```

## Folder Structure

  - `data/raw/` - Original CSVs downloaded from the Jolpica *dump*.
  - `data/processed/` - Artifacts ready for consumption (SQLite, views, reports).
  - `data/db_queries/` - Reusable SQL queries.
  - `notebooks/` - Exploratory analyses (`explore_data.ipynb`, `analise_verstappen.ipynb` etc.).
  - `src/data_processing/` - Ingestion and preparation scripts.
  - `src/data_viz/` - Visualization utilities.
  - `src/modules/` - Reusable components (e.g., `DbReader`).
  - `src/modules/features/` - Feature extraction logic (Pace, Reliability, Performance).
  - `data/features/` - Feature pipeline output (CSV files ready for use).

## Featured Notebooks

  - `notebooks/explore_data.ipynb` - Initial exploration of consolidated tables.
  - `notebooks/analise_verstappen.ipynb` - Study focused on Max Verstappen's performance (uses functions from `notebooks/utils.py`).
  - `notebooks/2025_championship` - Study focused on a retrospective and analysis of the 2025 championship.

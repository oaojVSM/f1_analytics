import sqlite3
import pandas as pd
from pathlib import Path

def load_csvs_to_sqlite(data_dir: Path, db_path: Path):
    conn = sqlite3.connect(db_path)

    for csv_file in data_dir.glob("*.csv"):
        table_name = csv_file.stem  # nome da tabela = nome do arquivo
        print(f"Importando {csv_file.name} para tabela '{table_name}'...")
        df = pd.read_csv(csv_file)
        df.to_sql(table_name, conn, if_exists="replace", index=False)

    conn.close()
    print(f"Banco criado em: {db_path}")

if __name__ == "__main__":
    raw_data_dir = Path(__file__).resolve().parents[2] / "data" / "raw"
    db_file = Path(__file__).resolve().parents[2] / "data" / "processed" / "f1.db"
    load_csvs_to_sqlite(raw_data_dir, db_file)

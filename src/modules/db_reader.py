import sqlite3
import pandas as pd
from pathlib import Path

class DbReader:
    def __init__(self, db_path=None):
        if db_path is None:
            # Caminho padrão: data/f1.db na raiz do projeto
            db_path = Path(__file__).resolve().parents[2] / "data" / "f1.db"
        self.db_path = Path(db_path)

    def run_query(self, sql: str, params: tuple = None) -> pd.DataFrame:
        """Executa uma query SQL e retorna um DataFrame do Pandas."""
        conn = sqlite3.connect(self.db_path)
        try:
            df = pd.read_sql_query(sql, conn, params=params)
        finally:
            conn.close()
        return df
    
    def run_query_file(self, filepath: str | Path, params: tuple | dict | None = None) -> pd.DataFrame:
        sql = Path(filepath).read_text(encoding="utf-8")
        return self.run_query(sql, params=params)


import sys
import os
import pandas as pd
from pathlib import Path

# Add project root to path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.append(str(project_root))

from src.modules.features.pace.extractor import PaceFeatureExtractor
from src.modules.features.performance.extractor import PerformanceFeatureExtractor
from src.modules.features.reliability.extractor import ReliabilityFeatureExtractor
from src.modules.data_processing.db_reader import DbReader
from src.modules.features import utils

def main():
    print("Initializing DbReader...")
    try:
        db = DbReader()
    except Exception as e:
        print(f"Error initializing DbReader: {e}")
        # Setup mock data if DB fails (fallback for environment without DB access)
        print("Using Mock Data due to DB failure or for testing.")
        # Create dummy dataframes...
        return

    print("Loading Data...")
    try:
        df_laps = db.run_query_file("data/db_queries/lap_times_report.sql")
        df_results = db.run_query_file("data/db_queries/race_results_report.sql")
        df_qualify = db.run_query_file("data/db_queries/qualify_report.sql")
    except Exception as e:
        print(f"Error loading SQL files: {e}")
        return

    print(f"Loaded Laps: {len(df_laps)}, Results: {len(df_results)}, Qualy: {len(df_qualify)}")

    # Prepare Raw for Pace (requires laps + qualify)
    pace_raw = {
        'lap_times': df_laps,
        'qualify_results': df_qualify
    }
    
    print("\n--- Testing Pace Extractor ---")
    pace_ext = PaceFeatureExtractor(pace_raw)
    try:
        df_pace = pace_ext.execute()
        print("Pace Extractor Success!")
        print(df_pace.head())
        print("Columns:", df_pace.columns.tolist())
        
        # Check specific values
        if not df_pace.empty:
            print(f"Average Pace Ratio vs Teammate (should be ~1.0): {df_pace['avg_pace_vs_teammate'].mean():.4f}")
    except Exception as e:
        print(f"Pace Extractor Failed: {e}")
        import traceback
        traceback.print_exc()

    # Prepare Raw for Performance
    perf_raw = {
        'race_results': df_results
    }
    
    print("\n--- Testing Performance Extractor ---")
    perf_ext = PerformanceFeatureExtractor(perf_raw)
    try:
        df_perf = perf_ext.execute()
        print("Performance Extractor Success!")
        print(df_perf.head())
    except Exception as e:
        print(f"Performance Extractor Failed: {e}")

    # Prepare Raw for Reliability
    rel_raw = {
        'race_results': df_results
    }
    
    print("\n--- Testing Reliability Extractor ---")
    rel_ext = ReliabilityFeatureExtractor(rel_raw)
    try:
        df_rel = rel_ext.execute()
        print("Reliability Extractor Success!")
        print(df_rel.head())
    except Exception as e:
        print(f"Reliability Extractor Failed: {e}")

if __name__ == "__main__":
    main()

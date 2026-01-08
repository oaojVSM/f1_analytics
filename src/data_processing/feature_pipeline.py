import sys
import os
import pandas as pd
from pathlib import Path

# Add project root to path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

from src.modules.data_processing.db_reader import DbReader
from src.modules.features.pace.extractor import PaceFeatureExtractor
from src.modules.features.performance.extractor import PerformanceFeatureExtractor
from src.modules.features.reliability.extractor import ReliabilityFeatureExtractor

def run_pipeline():
    print("Initializing Data Pipeline...")
    try:
        db = DbReader()
    except Exception as e:
        print(f"Error initializing DbReader: {e}")
        return

    print("Loading Raw Data from DB...")
    try:
        # Load data using SQL queries
        # Note: Paths are relative to project root where script should be run
        df_laps = db.run_query_file("data/db_queries/lap_times_report.sql")
        df_results = db.run_query_file("data/db_queries/race_results_report.sql")
        df_qualify = db.run_query_file("data/db_queries/qualify_report.sql")
        
        if df_laps.empty or df_results.empty or df_qualify.empty:
             print("Warning: One or more datasets are empty. Pipeline may produce incomplete results.")
             
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    print("Data Loaded. Starting Feature Extraction...")
    
    # 1. Pace Features
    print("Extracting Pace Features...")
    try:
        pace_raw = {'lap_times': df_laps, 'qualify_results': df_qualify}
        pace_ext = PaceFeatureExtractor(pace_raw)
        df_pace = pace_ext.execute()
    except Exception as e:
        print(f"Error extracting Pace features: {e}")
        df_pace = pd.DataFrame()
    
    # 2. Performance Features
    print("Extracting Performance Features...")
    try:
        perf_raw = {'race_results': df_results}
        perf_ext = PerformanceFeatureExtractor(perf_raw)
        df_perf = perf_ext.execute()
    except Exception as e:
        print(f"Error extracting Performance features: {e}")
        df_perf = pd.DataFrame()
    
    # 3. Reliability Features
    print("Extracting Reliability Features...")
    try:
        rel_raw = {'race_results': df_results}
        rel_ext = ReliabilityFeatureExtractor(rel_raw)
        df_rel = rel_ext.execute()
    except Exception as e:
        print(f"Error extracting Reliability features: {e}")
        df_rel = pd.DataFrame()
    
    # Saving Results
    output_dir = project_root / "data" / "features"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Saving features to {output_dir}...")
    
    if not df_pace.empty:
        output_path = output_dir / "pace_features.csv"
        df_pace.to_csv(output_path, index=False)
        print(f"Saved pace_features.csv ({len(df_pace)} rows)")
    else:
        print("Skipped saving pace_features.csv (Empty DataFrame)")
    
    if not df_perf.empty:
        output_path = output_dir / "performance_features.csv"
        df_perf.to_csv(output_path, index=False)
        print(f"Saved performance_features.csv ({len(df_perf)} rows)")
    else:
        print("Skipped saving performance_features.csv (Empty DataFrame)")
        
    if not df_rel.empty:
        output_path = output_dir / "reliability_features.csv"
        df_rel.to_csv(output_path, index=False)
        print(f"Saved reliability_features.csv ({len(df_rel)} rows)")
    else:
        print("Skipped saving reliability_features.csv (Empty DataFrame)")
        
    print("Pipeline Completed Successfully.")

if __name__ == "__main__":
    run_pipeline()
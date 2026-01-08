import pandas as pd
import numpy as np
from ..base import BaseFeatureExtractor
from ..utils import remove_invalid_laps

class PaceFeatureExtractor(BaseFeatureExtractor):
    def __init__(self, raw_data: dict):
        """
        Expects raw_data to contain:
        - 'lap_times': DataFrame from lap_times_report.sql
        - 'qualify_results': DataFrame from qualify_report.sql
        """
        super().__init__(raw_data)
        self.df_laps = raw_data.get('lap_times')
        self.df_qualify = raw_data.get('qualify_results')

    def _calculate_race_pace_metrics(self) -> pd.DataFrame:
        if self.df_laps is None or self.df_laps.empty:
            return pd.DataFrame()

        # Pre-process: Ensure lap_time_ms exists for the filter to work
        df_proc = self.df_laps.copy()
        if 'lap_time_ms' not in df_proc.columns and 'lap_time' in df_proc.columns:
             # Convert "MM:SS.ms" string to milliseconds
             # Using pd.to_timedelta with errors='coerce' to handle '1:23.456' format
             # Note: '0:' prefix might be needed if format is 'MM:SS.ms' and pandas expects 'HH:MM:SS'
             # but usually pandas is smart enough if minimal units are present.
             # However, F1 data often is '1:23.456'. 
             # Safe way: pd.to_timedelta('00:' + df['lap_time']) if needed, but let's try direct first.
             # Based on notebook utils, direct to_timedelta works.
             df_proc['lap_time_ms'] = pd.to_timedelta(df_proc['lap_time'], errors='coerce').dt.total_seconds() * 1000
             
        # 1. Filter invalid laps
        df_clean = remove_invalid_laps(df_proc)
        
        # 2. Check and Add lap_time_ms if still missing (redundant but safe)
        if 'lap_time_ms' not in df_clean.columns and 'lap_time' in df_clean.columns:
             df_clean['lap_time_ms'] = pd.to_timedelta(df_clean['lap_time'], errors='coerce').dt.total_seconds() * 1000

        # 3. Calculate basic metrics per (year, race_name, driver_id) first to get race context
        # We need race context (median of the field) BEFORE aggregating to driver/year
        
        # Group by Race to get Field stats
        race_stats = df_clean.groupby(['year', 'race_name'])['lap_time_ms'].agg(
            race_median_pace='median',
            race_avg_lap_time_std_dev='std' 
        ).reset_index()
        
        # Ratio = Driver / Team_Median. IF Driver is faster, Ratio < 1.
        # If Driver IS the median (e.g. he is the only one or dominant), it biases.
        # better: Calculate per driver, then join self on constructor to find pair.
        
        driver_race_stats = df_clean.groupby(['year', 'race_name', 'driver_id', 'constructor_name'])['lap_time_ms'].agg(
            driver_median_pace='median',
            driver_lap_time_std_dev='std',
            driver_p75='quantile' # q=0.75 needs lambda if not recent pandas, but 'quantile' works for 0.5 default.
        ).reset_index()
        
        # specific 75th percentile
        p75 = df_clean.groupby(['year', 'race_name', 'driver_id'])['lap_time_ms'].quantile(0.75).reset_index(name='driver_p75')
        driver_race_stats = driver_race_stats.drop(columns=['driver_p75'], errors='ignore').merge(p75, on=['year', 'race_name', 'driver_id'])

        # Merge field stats
        driver_race_stats = driver_race_stats.merge(race_stats, on=['year', 'race_name'])
        
        # Self-join for teammate
        # We look for another driver in same constructor, same race, same year.
        teammate_lookup = driver_race_stats[['year', 'race_name', 'constructor_name', 'driver_id', 'driver_median_pace', 'driver_lap_time_std_dev']].rename(
            columns={
                'driver_id': 'teammate_id', 
                'driver_median_pace': 'teammate_median_pace',
                'driver_lap_time_std_dev': 'teammate_lap_time_std_dev'
            }
        )
        
        driver_with_teammate = driver_race_stats.merge(teammate_lookup, on=['year', 'race_name', 'constructor_name'], how='inner')
        # Filter out self
        driver_with_teammate = driver_with_teammate[driver_with_teammate['driver_id'] != driver_with_teammate['teammate_id']]
        
        # Handle cases with > 2 drivers (rare in modern F1 but possible). 
        # We'll take the average of teammates if multiple, or just the first. 
        # Group by driver again to collapse multiple teammates (if any)
        driver_with_teammate = driver_with_teammate.groupby(['year', 'race_name', 'driver_id']).agg({
            'driver_median_pace': 'first',
            'driver_lap_time_std_dev': 'first',
            'driver_p75': 'first',
            'race_median_pace': 'first',
            'race_avg_lap_time_std_dev': 'first',
            'teammate_median_pace': 'median', # Median of teammates
            'teammate_lap_time_std_dev': 'mean'
        }).reset_index()

        # Metrics Calculation
        driver_with_teammate['pace_vs_field'] = driver_with_teammate['driver_median_pace'] / driver_with_teammate['race_median_pace']
        driver_with_teammate['pace_vs_teammate'] = driver_with_teammate['driver_median_pace'] / driver_with_teammate['teammate_median_pace']
        
        # Consistency Ratios
        driver_with_teammate['lap_time_std_dev_vs_field'] = driver_with_teammate['driver_lap_time_std_dev'] / driver_with_teammate['race_avg_lap_time_std_dev']
        driver_with_teammate['lap_time_std_dev_vs_teammate'] = driver_with_teammate['driver_lap_time_std_dev'] / driver_with_teammate['teammate_lap_time_std_dev']

        # Aggregation by Year/Driver
        final_stats = driver_with_teammate.groupby(['driver_id', 'year']).agg(
            avg_pace_vs_field=('pace_vs_field', 'mean'),
            avg_pace_vs_teammate=('pace_vs_teammate', 'mean'),
            avg_lap_time_std_dev_vs_field=('lap_time_std_dev_vs_field', 'mean'),
            avg_lap_time_std_dev_vs_teammate=('lap_time_std_dev_vs_teammate', 'mean'),
            avg_raw_lap_time_std_dev=('driver_lap_time_std_dev', 'mean')
        ).reset_index()
        
        return final_stats

    def _calculate_qualifying_metrics(self) -> pd.DataFrame:
        if self.df_qualify is None or self.df_qualify.empty:
            return pd.DataFrame()
            
        df = self.df_qualify.copy()
        
        # Ensure best_lap_time is numeric (convert from string if needed)
        if 'best_lap_time' in df.columns:
             # Check if string
             if df['best_lap_time'].dtype == object:
                 df['best_lap_time'] = pd.to_timedelta(df['best_lap_time'], errors='coerce').dt.total_seconds() * 1000
        
        # Determine Pole Position time (numeric min)
        pole_times = df.groupby(['year', 'race_name'])['best_lap_time'].min().reset_index(name='pole_time')
        
        df = df.merge(pole_times, on=['year', 'race_name'])
        
        # Teammate comparison
        teammate_lookup = df[['year', 'race_name', 'constructor_name', 'driver_id', 'best_lap_time']].rename(
            columns={'driver_id': 'teammate_id', 'best_lap_time': 'teammate_best_time'}
        )
        
        df_merged = df.merge(teammate_lookup, on=['year', 'race_name', 'constructor_name'], how='inner')
        df_merged = df_merged[df_merged['driver_id'] != df_merged['teammate_id']]
        
        # Collapse multiple teammates
        df_final = df_merged.groupby(['year', 'race_name', 'driver_id']).agg({
             'best_lap_time': 'first',
             'pole_time': 'first',
             'teammate_best_time': 'min' # Validate against the BEST teammate
        }).reset_index()
        
        # Calculations
        # % Gap. (Driver - Target) / Target. 
        # Lower is better (if negative, you beat them, but usually we look at positive gaps for slower drivers)
        # But commonly in F1: (DriverTime / PoleTime) - 1  => Percentage off pole. 
        
        df_final['gap_to_pole_pct'] = (df_final['best_lap_time'] / df_final['pole_time']) - 1.0
        df_final['gap_to_teammate_pct'] = (df_final['best_lap_time'] / df_final['teammate_best_time']) - 1.0
        
        # Aggregation
        agg_stats = df_final.groupby(['driver_id', 'year']).agg(
            avg_qualifying_gap_to_pole_pct=('gap_to_pole_pct', 'mean'),
            avg_qualifying_gap_to_teammate_pct=('gap_to_teammate_pct', 'mean')
        ).reset_index()
        
        return agg_stats

    def execute(self) -> pd.DataFrame:
        race_stats = self._calculate_race_pace_metrics()
        qualy_stats = self._calculate_qualifying_metrics()
        
        if race_stats.empty and qualy_stats.empty:
            return pd.DataFrame()
        
        if race_stats.empty:
            return qualy_stats
            
        if qualy_stats.empty:
            return race_stats
            
        # Merge
        merged = pd.merge(race_stats, qualy_stats, on=['driver_id', 'year'], how='outer')
        return merged

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
        self.stint_counts = None

    def _filter_short_stint_drivers(self):
        """
        Removes drivers who have participated in <= 2 races for a specific constructor in a year.
        Uses shared utility.
        """
        from ..utils import get_valid_stints
        
        valid_stints, self.stint_counts = get_valid_stints([self.df_laps, self.df_qualify])
        
        if valid_stints.empty:
            return

        # Filter df_laps
        if self.df_laps is not None and not self.df_laps.empty:
            self.df_laps = self.df_laps.merge(
                valid_stints, 
                on=['year', 'constructor_name', 'driver_id'], 
                how='inner'
            )

        # Filter df_qualify
        if self.df_qualify is not None and not self.df_qualify.empty:
            self.df_qualify = self.df_qualify.merge(
                valid_stints, 
                on=['year', 'constructor_name', 'driver_id'], 
                how='inner'
            )


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
        
        # Calculate Driver Stats:
        # Consistency is calculated as the Average of Per-Stint Standard Deviations
        # This isolates tyre compounds/fuel loads per stint.
        
        # Stint-level consistency
        if 'stint_number' not in df_clean.columns:
             # Fallback if stint_number missing (should not happen with new query)
             current_stint_std = df_clean.groupby(['year', 'race_name', 'driver_id', 'constructor_name'])['lap_time_ms'].std().reset_index(name='driver_lap_time_std_dev')
        else:
             stint_std = df_clean.groupby(['year', 'race_name', 'driver_id', 'constructor_name', 'stint_number'])['lap_time_ms'].std().reset_index(name='stint_std_dev')
             # Average of stint std devs per driver/race
             current_stint_std = stint_std.groupby(['year', 'race_name', 'driver_id', 'constructor_name'])['stint_std_dev'].mean().reset_index(name='driver_lap_time_std_dev')

        # Driver Median Pace (Overall)
        driver_median = df_clean.groupby(['year', 'race_name', 'driver_id', 'constructor_name'])['lap_time_ms'].median().reset_index(name='driver_median_pace')
        
        driver_race_stats = driver_median.merge(current_stint_std, on=['year', 'race_name', 'driver_id', 'constructor_name'])
        
        # Field Stats (Average of the drivers' consistent scores)
        race_stats = driver_race_stats.groupby(['year', 'race_name']).agg(
            race_median_pace=('driver_median_pace', 'median'),
            race_avg_lap_time_std_dev=('driver_lap_time_std_dev', 'mean') # Average consistency of the field
        ).reset_index()
        
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
        # We pick the teammate with the most races in that team/year to be the stable benchmark.
        
        if self.stint_counts is not None:
             teammate_counts = self.stint_counts.rename(columns={'driver_id': 'teammate_id', 'race_count': 'teammate_races'})
             driver_with_teammate = driver_with_teammate.merge(teammate_counts, on=['year', 'constructor_name', 'teammate_id'], how='left')
             
             # Sort by teammate experience (descending)
             driver_with_teammate.sort_values(by=['year', 'race_name', 'driver_id', 'teammate_races'], ascending=[True, True, True, False], inplace=True)

        # Collapse multiple teammates by taking the first one (most experienced)
        driver_with_teammate = driver_with_teammate.drop_duplicates(subset=['year', 'race_name', 'driver_id'], keep='first')
        
        # Merge Field Stats
        driver_with_teammate = driver_with_teammate.merge(race_stats, on=['year', 'race_name'], how='left')

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
        # Prioritize teammate with most races
        if self.stint_counts is not None:
             teammate_counts = self.stint_counts.rename(columns={'driver_id': 'teammate_id', 'race_count': 'teammate_races'})
             df_merged = df_merged.merge(teammate_counts, on=['year', 'constructor_name', 'teammate_id'], how='left')
             # Sort
             df_merged.sort_values(by=['year', 'race_name', 'driver_id', 'teammate_races'], ascending=[True, True, True, False], inplace=True)
             
        df_final = df_merged.drop_duplicates(subset=['year', 'race_name', 'driver_id'], keep='first').copy()
        
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
        # 0. Filter Short Stints
        self._filter_short_stint_drivers()

        race_stats = self._calculate_race_pace_metrics()
        qualy_stats = self._calculate_qualifying_metrics()
        
        merged = pd.DataFrame()
        if race_stats.empty and qualy_stats.empty:
            return pd.DataFrame()
        elif race_stats.empty:
            merged = qualy_stats
        elif qualy_stats.empty:
            merged = race_stats
        else:
            merged = pd.merge(race_stats, qualy_stats, on=['driver_id', 'year'], how='outer')

        # Add Metadata (Names, Team)
        # Combine distinct metadata from both sources to ensure coverage (e.g. drivers who only qualified)
        meta_dfs = []
        
        for df_source in [self.df_laps, self.df_qualify]:
            if df_source is not None and not df_source.empty:
                 req_cols = ['driver_id', 'year', 'driver_full_name', 'driver_surname', 'constructor_name']
                 available_cols = [c for c in req_cols if c in df_source.columns]
                 
                 if 'driver_id' in available_cols and 'year' in available_cols:
                     grp = df_source.groupby(['driver_id', 'year']).agg({
                        'driver_full_name': 'first',
                        'driver_surname': 'first',
                        'constructor_name': lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0]
                     }).reset_index()
                     meta_dfs.append(grp)
        
        if meta_dfs:
            # Concat and drop duplicates (keep first found)
            meta_combined = pd.concat(meta_dfs).drop_duplicates(subset=['driver_id', 'year'])
            
            merged = merged.merge(meta_combined, on=['driver_id', 'year'], how='left')
            
            # Reorder columns to put metadata first
            cols = merged.columns.tolist()
            meta_cols = ['driver_id', 'year', 'driver_full_name', 'driver_surname', 'constructor_name']
            # Filter meta_cols in case some are missing
            meta_cols = [c for c in meta_cols if c in cols]
            other_cols = [c for c in cols if c not in meta_cols]
            merged = merged[meta_cols + other_cols]

        return merged

import pandas as pd
import numpy as np
from ..base import BaseFeatureExtractor

class PerformanceFeatureExtractor(BaseFeatureExtractor):
    def __init__(self, raw_data: dict):
        """
        Expects raw_data to contain:
        - 'race_results': DataFrame from race_results_report.sql
        """
        super().__init__(raw_data)
        self.df_results = raw_data.get('race_results')

    def execute(self) -> pd.DataFrame:
        if self.df_results is None or self.df_results.empty:
            return pd.DataFrame()

        df = self.df_results.copy()
        
        # Ensure numeric columns
        cols_to_numeric = ['finishing_position', 'starting_position', 'points_scored']
        for col in cols_to_numeric:
            if col in df.columns:
                 df[col] = pd.to_numeric(df[col], errors='coerce')

        # 1. Basic Performance Metrics per Race
        df['positions_gained'] = df['starting_position'] - df['finishing_position']
        
        # 2. Teammate Comparisons (Points & Qualy Head-to-Head)
        # Identify teammate by year, race, constructor
        
        # Simplification: We will aggregation everything to (driver_id, year) directly 
        # but for teammate ratios we need values per race or total points per year comparison.
        
        # Total Points per Year per Driver
        driver_yearly = df.groupby(['year', 'driver_id', 'constructor_name']).agg(
            total_points=('points_scored', 'sum'),
            avg_finish=('finishing_position', 'mean'),
            avg_grid=('starting_position', 'mean'),
            avg_gained=('positions_gained', 'mean'),
            races_count=('race_name', 'nunique')
        ).reset_index()
        
        # Now find teammate yearly totals (assuming staying in same team, which is tricky for mid-season transfers)
        # A better way for Points Ratio: Sum points for Driver, Sum points for Team, Ratio = Driver/Team
        
        team_yearly = df.groupby(['year', 'constructor_name']).agg(
            team_total_points=('points_scored', 'sum')
        ).reset_index()
        
        # Merge driver yearly with team yearly
        merged = driver_yearly.merge(team_yearly, on=['year', 'constructor_name'])
        
        # Points Share
        # Avoid division by zero
        merged['points_share_of_team'] = merged.apply(
            lambda x: x['total_points'] / x['team_total_points'] if x['team_total_points'] > 0 else 0, axis=1
        )
        
        # Points per Race
        merged['points_per_race'] = merged['total_points'] / merged['races_count']
        
        # Qualy Head-to-Head (Grid Position)
        # We need race-by-race comparison for this
        # Let's go back to race-level stats
        race_level = df[['year', 'race_name', 'constructor_name', 'driver_id', 'starting_position']].copy()
        
        teammate_lookup = race_level.rename(columns={'driver_id': 'teammate_id', 'starting_position': 'teammate_start'})
        
        race_merged = race_level.merge(teammate_lookup, on=['year', 'race_name', 'constructor_name'])
        race_merged = race_merged[race_merged['driver_id'] != race_merged['teammate_id']]
        
        # Head to Head: Did I start ahead? (Lower is better)
        race_merged['qualified_ahead'] = race_merged['starting_position'] < race_merged['teammate_start']
        
        # Aggregating H2H
        h2h_stats = race_merged.groupby(['year', 'driver_id']).agg(
            qualy_h2h_wins=('qualified_ahead', 'sum'),
            qualy_h2h_total=('qualified_ahead', 'count')
        ).reset_index()
        
        h2h_stats['qualy_vs_teammate_win_rate'] = h2h_stats['qualy_h2h_wins'] / h2h_stats['qualy_h2h_total']
        
        # Final aggregation
        # Start with the merged yearly stats (which might be split by constructor if driver changed teams)
        # We want one row per driver per year.
        
        # Weighted average for points share if multiple teams? 
        # Or just sum totals. 
        # Let's re-aggregate 'merged' by driver/year
        
        final_agg = merged.groupby(['driver_id', 'year']).agg(
            total_points=('total_points', 'sum'),
            avg_finish_pos=('avg_finish', 'mean'), # Weighted? simplified mean for now
            avg_grid_pos=('avg_grid', 'mean'),
            avg_positions_gained=('avg_gained', 'mean'),
            points_per_race=('points_per_race', 'mean'),
            # For points share, we can verify if it makes sense to average shares or recompute
            # Recomputing: DriverTotal / Sum(TeamTotalsOfStints). 
            # Simplified: Mean of share
            avg_points_share=('points_share_of_team', 'mean')
        ).reset_index()
        
        # Add H2H
        final_agg = final_agg.merge(h2h_stats[['year', 'driver_id', 'qualy_vs_teammate_win_rate']], on=['year', 'driver_id'], how='left')
        
        return final_agg

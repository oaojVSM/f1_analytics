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

    def _filter_short_stint_drivers(self):
        """
        Removes drivers who have participated in <= 2 races for a specific constructor in a year.
        Uses shared utility.
        """
        if self.df_results is None or self.df_results.empty:
            return

        from ..utils import get_valid_stints
        
        valid_stints, self.stint_counts = get_valid_stints([self.df_results])
        
        if valid_stints.empty:
            return

        # Filter df_results to only keep valid stints
        self.df_results = self.df_results.merge(
            valid_stints, 
            on=['year', 'constructor_name', 'driver_id'], 
            how='inner'
        )

    def execute(self) -> pd.DataFrame:
        if self.df_results is None or self.df_results.empty:
            return pd.DataFrame()

        # 0. Filter Short Stints
        # self._filter_short_stint_drivers()
        
        if self.df_results.empty:
             return pd.DataFrame()

        df = self.df_results.copy()

        # Only get main event data:
        df = df[df['session_type'] == 'R']
        
        # Ensure numeric columns
        cols_to_numeric = ['finishing_position', 'starting_position', 'points_scored']
        for col in cols_to_numeric:
            if col in df.columns:
                 df[col] = pd.to_numeric(df[col], errors='coerce')

        # 1. Basic Performance Metrics per Race
        df['positions_gained'] = df['starting_position'] - df['finishing_position']
        
        # 2. Teammate Comparisons
        # Calculate Teammate comparisons per race to get diffs
        # Comparison Columns: Finishing Position, Starting Position (Grid)
        
        race_level = df[['year', 'race_name', 'constructor_name', 'driver_id', 'starting_position', 'finishing_position', 'points_scored']].copy()
        
        teammate_lookup = race_level.rename(columns={
            'driver_id': 'teammate_id', 
            'starting_position': 'teammate_start',
            'finishing_position': 'teammate_finish',
            'points_scored': 'teammate_points'
        })
        
        race_merged = race_level.merge(teammate_lookup, on=['year', 'race_name', 'constructor_name'])
        # Filter self
        race_merged = race_merged[race_merged['driver_id'] != race_merged['teammate_id']]
        
        # # Handle multiple teammates: Prioritize teammate with most races in that stint
        # if self.stint_counts is not None:
        #      teammate_counts = self.stint_counts.rename(columns={'driver_id': 'teammate_id', 'race_count': 'teammate_races'})
        #      race_merged = race_merged.merge(teammate_counts, on=['year', 'constructor_name', 'teammate_id'], how='left')
        #      # Sort by teammate experience (descending)
        #      race_merged.sort_values(by=['year', 'race_name', 'driver_id', 'teammate_races'], ascending=[True, True, True, False], inplace=True)
             
        # # Collapse multiple teammates (keep first/most experienced)
        # race_merged = race_merged.drop_duplicates(subset=['year', 'race_name', 'driver_id'], keep='first')
        
        # Metrics Calculation
        race_merged['qualified_ahead'] = race_merged['starting_position'] < race_merged['teammate_start']
        race_merged['finished_ahead'] = race_merged['finishing_position'] < race_merged['teammate_finish']
        
        race_merged['grid_pos_diff'] = race_merged['starting_position'] - race_merged['teammate_start']
        race_merged['finish_pos_diff'] = race_merged['finishing_position'] - race_merged['teammate_finish']
        race_merged['points_diff'] = race_merged['points_scored'] - race_merged['teammate_points']

        # Aggregating H2H and Diffs
        h2h_stats = race_merged.groupby(['year', 'driver_id']).agg(
            qualy_h2h_wins=('qualified_ahead', 'sum'),
            race_h2h_wins=('finished_ahead', 'sum'),
            total_h2h_races=('race_name', 'count'),
            starting_pos_diff_vs_tmate=('grid_pos_diff', 'mean'), # Negativo = Largou na frente em média
            finish_pos_diff_vs_tmate=('finish_pos_diff', 'mean'), # Negativo = Chegou na frente em média
            points_obtained_diff_vs_tmate=('points_diff', 'mean') # Positivo = Fez mais pontos
        ).reset_index()
        
        h2h_stats['qualy_vs_teammate_win_rate'] = h2h_stats['qualy_h2h_wins'] / h2h_stats['total_h2h_races']
        h2h_stats['race_vs_teammate_win_rate'] = h2h_stats['race_h2h_wins'] / h2h_stats['total_h2h_races']

        # Remove coluna que foi usada para calculos mas que não é uma feature interessante por si só
        h2h_stats = h2h_stats.drop(columns=['total_h2h_races'])
        
        # 3. Yearly Aggregation (General)
        # Total Points per Year per Driver
        driver_yearly = df.groupby(['year', 'driver_id', 'constructor_name']).agg(
            total_points=('points_scored', 'sum'),
            avg_finish=('finishing_position', 'mean'),
            avg_grid=('starting_position', 'mean'),
            avg_gained=('positions_gained', 'mean'),
            races_count=('race_name', 'nunique')
        ).reset_index()
        
        team_yearly = df.groupby(['year', 'constructor_name']).agg(
            team_total_points=('points_scored', 'sum')
        ).reset_index()
        
        merged = driver_yearly.merge(team_yearly, on=['year', 'constructor_name'])
        
        merged['points_share_of_team'] = merged.apply(
            lambda x: x['total_points'] / x['team_total_points'] if x['team_total_points'] > 0 else 0, axis=1
        )
        
        merged['points_per_race'] = merged['total_points'] / merged['races_count']
        
        year_driver_agg = merged.groupby(['driver_id', 'year']).agg(
            total_points=('total_points', 'sum'),
            avg_finish_pos=('avg_finish', 'mean'),
            avg_grid_pos=('avg_grid', 'mean'),
            avg_positions_gained=('avg_gained', 'mean'),
            points_per_race=('points_per_race', 'mean'),
            team_points_share=('points_share_of_team', 'mean') # Aqui faço a média pra lidar com os poucos casos que trocam de equipe ao longo do ano. Mas pros outros pilotos (grande maioria) isso retorna o próprio percentual.
        ).reset_index()
        
        # Merge H2H
        final_agg = year_driver_agg.merge(h2h_stats, on=['year', 'driver_id'], how='left')

        # Add Metadata (Names, Team)
        if self.df_results is not None and not self.df_results.empty:
            req_cols = ['driver_id', 'year', 'driver_full_name', 'driver_surname', 'constructor_name']
            available_cols = [c for c in req_cols if c in self.df_results.columns]
            
            if 'driver_id' in available_cols and 'year' in available_cols:
                meta = self.df_results.groupby(['driver_id', 'year']).agg({
                    'driver_full_name': 'first',
                    'driver_surname': 'first',
                    'constructor_name': lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0]
                }).reset_index()
                
                final_agg = final_agg.merge(meta, on=['driver_id', 'year'], how='left')
                
                # Reorder
                cols = final_agg.columns.tolist()
                meta_cols = ['driver_id', 'year', 'driver_full_name', 'driver_surname', 'constructor_name']
                meta_cols = [c for c in meta_cols if c in cols]
                other_cols = [c for c in cols if c not in meta_cols]
                final_agg = final_agg[meta_cols + other_cols]

        return final_agg

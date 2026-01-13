import pandas as pd
import numpy as np
from ..base import BaseFeatureExtractor
from ..utils import get_valid_stints

class ExperienceFeatureExtractor(BaseFeatureExtractor):
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
        cols_to_numeric = ['finishing_position', 'starting_position']
        for col in cols_to_numeric:
            if col in df.columns:
                 df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Ensure correct sorting for cumulative calculation
        # Sort by Year and Round (Race Date implicitly)
        # Assuming r.number or race_date is available. 
        # race_results_report has 'year' and 'round_id' (but round_id might not be ordered? query says r.number ASC)
        # The query sorts by Year DESC, Round Number ASC.
        # We need Ascending Year for cumulative sum.
        
        df = df.sort_values(by=['year', 'round_id']) # Using round_id as proxy for chronological order if available, or just year is not enough if we want to be precise, but we aggregate by year anyway.
        # Ideally, we calculate stats UP TO the end of that year.
        
        # Define Event Columns
        df['is_win'] = df['finishing_position'] == 1
        df['is_podium'] = df['finishing_position'] <= 3
        df['is_pole'] = df['starting_position'] == 1
        df['is_race_start'] = True # If they are in race results (Finished, DNF etc), they started. (Excluding DNS/Did Not Qualify if filtered, but reliability extractor handles that detailed status)
                                   # We will assume entries in this table are starts or at least participation.
        
        # Group by Driver and Year to get yearly totals first
        yearly_stats = df.groupby(['driver_id', 'year']).agg(
            yearly_races=('is_race_start', 'count'),
            yearly_wins=('is_win', 'sum'),
            yearly_podiums=('is_podium', 'sum'),
            yearly_poles=('is_pole', 'sum')
        ).reset_index()
        
        # Sort by driver and year to cumulative sum
        yearly_stats = yearly_stats.sort_values(by=['driver_id', 'year'])
        
        # Calculate Cumulative Stats (Career stats at END of that year)
        yearly_stats['career_races'] = yearly_stats.groupby('driver_id')['yearly_races'].cumsum()
        yearly_stats['career_wins'] = yearly_stats.groupby('driver_id')['yearly_wins'].cumsum()
        yearly_stats['career_podiums'] = yearly_stats.groupby('driver_id')['yearly_podiums'].cumsum()
        yearly_stats['career_poles'] = yearly_stats.groupby('driver_id')['yearly_poles'].cumsum()
        
        # Calculate Years in F1 (Experience)
        # Simply row number per driver? 
        # Yes, if we have a row for each year.
        yearly_stats['years_in_f1'] = yearly_stats.groupby('driver_id').cumcount() + 1
        
        # Select final columns
        final_df = yearly_stats[[
            'driver_id', 'year', 
            'career_races', 'career_wins', 'career_podiums', 
            'career_poles', 'years_in_f1'
        ]]
        
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
                
                final_df = final_df.merge(meta, on=['driver_id', 'year'], how='left')
                
                # Reorder
                cols = final_df.columns.tolist()
                meta_cols = ['driver_id', 'year', 'driver_full_name', 'driver_surname', 'constructor_name']
                meta_cols = [c for c in meta_cols if c in cols]
                other_cols = [c for c in cols if c not in meta_cols]
                final_df = final_df[meta_cols + other_cols]

        return final_df

import pandas as pd
from ..base import BaseFeatureExtractor

class ReliabilityFeatureExtractor(BaseFeatureExtractor):
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
        
        df['race_status'] = pd.to_numeric(df['race_status'], errors='coerce').fillna(-1)

        # Status Codes:
        # 0: Finished
        # 1: Finished Lap(s) behind
        # 10: Accident/Collision
        # 11: Mechanical/Safety/Retirement
        # 20: Disqualified
        # 30: Withdrawn/DNS
        # 40/41: DNQ
        
        # Definition of DNF: Anything that is not Finished (0 or 1).
        df['is_dnf'] = ~df['race_status'].isin([0, 1])
        
        # Mechanical DNF: Status 11
        df['is_mechanical_dnf'] = df['race_status'] == 11
        
        # Accident DNF: Status 10
        df['is_accident_dnf'] = df['race_status'] == 10
        
        # Aggregation by Year/Driver
        agg = df.groupby(['driver_id', 'year']).agg(
            total_races=('race_name', 'count'),
            total_dnf=('is_dnf', 'sum'),
            total_mech_dnf=('is_mechanical_dnf', 'sum'),
            total_accident_dnf=('is_accident_dnf', 'sum')
        ).reset_index()
        
        agg['dnf_rate'] = agg['total_dnf'] / agg['total_races']
        agg['mechanical_dnf_rate'] = agg['total_mech_dnf'] / agg['total_races']
        agg['accident_dnf_rate'] = agg['total_accident_dnf'] / agg['total_races']
        
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
                
                agg = agg.merge(meta, on=['driver_id', 'year'], how='left')
                
                # Reorder
                cols = agg.columns.tolist()
                meta_cols = ['driver_id', 'year', 'driver_full_name', 'driver_surname', 'constructor_name']
                meta_cols = [c for c in meta_cols if c in cols]
                other_cols = [c for c in cols if c not in meta_cols]
                agg = agg[meta_cols + other_cols]

        return agg

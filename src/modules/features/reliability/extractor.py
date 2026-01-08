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
        
        # Determine DNF
        # Status 'Finished' (ID 1 usually) or '+1 Lap' etc are NOT DNFs.
        # Everything else usually is.
        # But we need to distinguish Mechanical vs Accident.
        
        # Common Status IDs (Standard Ergast/Jolpica mapping assumption, better to check strings if available)
        # The query returns 'race_status' string.
        
        # Finished strings: 'Finished', '+1 Lap', '+2 Laps', ...
        # If status starts with '+' or is 'Finished', it's not a DNF.
        # (Be careful with 'Disqualified')
        
        def is_dnf(status):
            s = str(status).lower()
            if s == 'finished': return False
            if s.startswith('+'): return False
            return True

        def is_mechanical_dnf(status):
            s = str(status).lower()
            if not is_dnf(status): return False
            
            # Keywords for accidents/collisions
            collision_keywords = ['collision', 'accident', 'spun', 'run off', 'disqualified', 'excluded', 'retired', 'withdrew']
            # 'retired' is vague, but often implies mechanical if not accident. 
            # However, in many datasets 'Retired' is capable of being anything.
            # Let's list known Mechanical keywords strictly.
            mech_keywords = ['engine', 'gearbox', 'transmission', 'clutch', 'hydraulics', 'electrical', 'brakes', 'suspension', 'overheating', 'mechanical', 'power unit', 'ers', 'turbo', 'exhaust', 'oil', 'pump', 'battery']
            
            for k in mech_keywords:
                if k in s:
                    return True
            return False

        df['is_dnf'] = df['race_status'].apply(is_dnf)
        df['is_mechanical_dnf'] = df['race_status'].apply(is_mechanical_dnf)
        
        # Aggregation by Year/Driver
        agg = df.groupby(['driver_id', 'year']).agg(
            total_races=('race_name', 'count'),
            total_dnf=('is_dnf', 'sum'),
            total_mech_dnf=('is_mechanical_dnf', 'sum')
        ).reset_index()
        
        agg['dnf_rate'] = agg['total_dnf'] / agg['total_races']
        agg['mechanical_dnf_rate'] = agg['total_mech_dnf'] / agg['total_races']
        
        return agg

from typing import Dict, Optional, Union, List
import pandas as pd
import numpy as np

class PointsNormalizer:
    """
    Responsável por normalizar pontuações históricas para sistemas modernos
    e projetar pontuações baseadas no tamanho do calendário.
    """

    SCORING_MODERN_25 = {
        1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
        6: 8,  7: 6,  8: 4,  9: 2,  10: 1
    }

    def __init__(self, 
                 scoring_system: Optional[Dict[int, int]] = None, 
                 target_rounds: int = 24):
        """
        Args:
            scoring_system: Dic {posicao: pontos}. Se None, usa padrão 2025.
            target_rounds: Inteiro para projetar a 'Inflação de Calendário' (padrão 24).
        """
        self.scoring_map = scoring_system if scoring_system else self.SCORING_MODERN_25
        self.target_rounds = target_rounds

    def calculate_points(self, position: Union[int, float], fastest_lap: bool = False) -> float:
        """
        Calcula pontos para uma única posição de chegada.
        
        Args:
            position: Posição de chegada (int).
            fastest_lap: Se fez a volta mais rápida (bool).
        
        Returns:
            float: Pontos calculados.
        """
        # Trata NaNs ou valores inválidos (DNF costuma vir como NaN ou string)
        if pd.isna(position) or isinstance(position, str):
            return 0.0
            
        try:
            pos = int(position)
        except ValueError:
            return 0.0
        
        points = self.scoring_map.get(pos, 0)
        
        # Regra de FL (Geralmente só conta se estiver no Top 10)
        # Se você estiver usando regras de 2025, FL não dá ponto, então basta não passar True.
        if fastest_lap and pos <= 10 and points > 0:
            points += 1
            
        return float(points)

    def normalize_points_by_number_of_rounds(self, current_points: float, actual_rounds: int) -> float:
        """
        Projeta a pontuação para o calendário alvo (Extrapolação).
        Ex: Se fez 100 pts em 10 corridas, faria 240 em 24.
        """
        if actual_rounds <= 0:
            return 0.0
        
        ratio = self.target_rounds / actual_rounds
        return current_points * ratio

    def apply_scoring_pandas(self, 
                         positions: pd.Series, 
                         fastest_laps: Optional[pd.Series] = None) -> pd.Series:
        """
        Helper otimizado para Pandas. Aplica a pontuação em uma coluna inteira.
        """
        # Mapeamento direto é muito mais rápido que apply()
        # fillna(0) garante que posições não mapeadas (DNFs, >10) virem 0
        points_series = positions.map(self.scoring_map).fillna(0)
        
        if fastest_laps is not None:
            # Adiciona 1 ponto se FL=True E estiver na zona de pontuação
            fl_points = (fastest_laps & (points_series > 0)).astype(int)
            points_series += fl_points
            
        return points_series
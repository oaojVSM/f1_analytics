from typing import Tuple, Union, Optional
import pandas as pd
import numpy as np

class FeatureNormalizer:
    """
    A robust feature normalization utility for F1 analytics.
    
    This class provides methods to normalize data using various strategies,
    with a focus on handling outliers and ensuring data falls within a specific range.
    """

    @staticmethod
    def z_score(series: pd.Series) -> pd.Series:
        """
        Calculates the Z-Score (standardization) of a pandas Series.
        
        Formula: z = (x - mean) / std
        
        Args:
            series (pd.Series): The input data series.
            
        Returns:
            pd.Series: The standardized series. Returns strings of 0.0 if stdev is 0.
        """
        if series.empty:
            return series

        mean = series.mean()
        std = series.std()

        if std == 0:
            return pd.Series(0.0, index=series.index)

        return (series - mean) / std

    @staticmethod
    def min_max(series: pd.Series, target_range: Tuple[float, float] = (0, 1)) -> pd.Series:
        """
        Scales a pandas Series to a specific range using Min-Max scaling.
        
        Args:
            series (pd.Series): The input data series.
            target_range (Tuple[float, float]): The target (min, max) range.
            
        Returns:
            pd.Series: The scaled series.
        """
        if series.empty:
            return series

        series_min = series.min()
        series_max = series.max()
        
        target_min, target_max = target_range

        if series_max == series_min:
            # If all values are the same, return the midpoint of the target range 
            # or the min if range is 0.
            return pd.Series(target_min, index=series.index)
        
        # Min-Max Scaling Formula:
        # X_std = (X - X.min) / (X.max - X.min)
        # X_scaled = X_std * (max - min) + min
        
        return (series - series_min) / (series_max - series_min) * (target_max - target_min) + target_min

    @classmethod
    def robust_normalize(
        cls, 
        series: pd.Series, 
        target_range: Tuple[float, float] = (0, 1),
        clip_outliers_sigma: Optional[float] = None,
        lower_is_better: bool = False
    ) -> pd.Series:
        """
        Applies a robust normalization strategy:
        1. (Optional) Z-Score standardization.
        2. (Optional) Clipping of extreme Z-scores (e.g., beyond 3 sigma).
        3. Min-Max scaling to the final target range.
        
        This method is designed to be the default 'robust' choice. It first standardizes
        the distribution to center it around 0 with unit variance, potentially handles extreme
        outliers, and then projects it onto a fixed scale (0-100, 0-1, etc.).

        Args:
            series (pd.Series): The input data.
            target_range (Tuple[float, float]): The desired output range.
            clip_outliers_sigma (Optional[float]): If set (e.g., 3.0), values with a Z-Score
                                                   magnitude greater than this will be clipped
                                                   before min-max scaling. This prevents extreme
                                                   outliers from compressing the rest of the data.
            lower_is_better (bool): If True, the logic is inverted so that lower values in the 
                                    input series result in higher normalized scores.
                                    Useful for metrics like Lap Time or Gap to Leader.

        Returns:
            pd.Series: The normalized series.
        """
        if series.empty:
            return series

        # 0. Handle Directionality
        # If lower is better, we invert the series so that lower values become higher numbers.
        # This way, existing Z-Score and Min-Max logic will naturally assign higher scores to "better" (lower) original values.
        working_series = series.copy()
        if lower_is_better:
            working_series = -working_series

        # 1. Z-Score Standardization
        z_scored = cls.z_score(working_series)
        
        # 2. Outlier Clipping (optional but recommended for "robustness")
        data_to_scale = z_scored
        if clip_outliers_sigma is not None:
            data_to_scale = data_to_scale.clip(lower=-clip_outliers_sigma, upper=clip_outliers_sigma)
            
        # 3. Min-Max Scaling
        # We apply min-max on the Z-scored (and potentially clipped) data
        # to ensure the final output strictly adheres to target_range.
        return cls.min_max(data_to_scale, target_range=target_range)

import pandas as pd
from src.analysis.utils.feature_normalizer import FeatureNormalizer
from src.analysis.data_viz.constants import JOLPICA_CONSTRUCTOR_RENAME

def filter_year(df_features: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    Filters a DataFrame to include only the specified year.
    """
    return df_features[df_features['year'] == year]

def replace_constructors_names(df_features: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces constructor names with abbreviations.
    """
    df_features['constructor_name'] = df_features['constructor_name'].replace(JOLPICA_CONSTRUCTOR_RENAME)
    return df_features


def get_features_column_list(df_features: pd.DataFrame) -> list[str]:
    """
    Returns a list of feature column names from a DataFrame.
    """

    list_non_feature_columns = [
        "driver_id",
        "year",
        "driver_full_name",
        "driver_surname",
        "constructor_name"
    ]
    return [col for col in df_features.columns if col not in list_non_feature_columns]


def create_normalized_features(df_features: pd.DataFrame, min_val: float = 5, max_val: float = 10, normalizer: FeatureNormalizer = FeatureNormalizer()) -> pd.DataFrame:
    """
    Creates normalized features from a DataFrame.
    """
    df_normalized = df_features.copy()
    for col in get_features_column_list(df_features):
        df_normalized[f'{col}_norm'] = normalizer.robust_normalize(df_features[col], target_range=(min_val, max_val))
    return df_normalized
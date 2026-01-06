import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from dateutil.relativedelta import relativedelta
from matplotlib.patches import Rectangle
from typing import Optional, Tuple, List
import os

def _identify_sc_laps(
    df_laps: pd.DataFrame,
    threshold_percent: float = 1.20,
    group_cols = ['year', 'race_name']
) -> pd.DataFrame:
    """
    Identifies probable Safety Car (or VSC) laps in a DataFrame with multiple races.

    The logic is based on the fact that during an SC, lap times for all drivers
    increase significantly. The function calculates a baseline race pace for each
    race and flags laps where the median time is much higher than this pace.
    It also checks if the driver lost positions in the following lap; if they did,
    it might be a driver error, so the lap is kept (not marked as SC).

    Originally, I analyzed the general lap median VS general race median, but it didn't work well
    as it flagged many laps that didn't make sense. The only consistent way was
    taking the race median and comparing it with each driver's lap, including the position loss check.

    Parameters
    ----------
    df_laps : pd.DataFrame
        DataFrame containing lap times for one or more races.
        Must contain columns 'lap_number', 'lap_time_ms', 'is_pit_lap'.
    threshold_percent : float, default 1.20
        The percentage above the baseline pace to consider a lap as SC.
        For example, 1.20 means the lap median must be 20% slower than the race median.
    group_cols : list, default ['year', 'race_name']
        Columns to group by for calculating baseline pace.

    Returns
    -------
    pd.DataFrame
        A copy of the original DataFrame with the new column 'is_safety_car_lap'.
    """
    df_out = df_laps.copy()

    # 1. Filtrar voltas que não representam ritmo de corrida (pit stops, 1ª volta)
    df_racing_laps = df_out.query("is_pit_lap == 0 and lap_number > 1").copy()

    # 2. Calcular o ritmo de corrida base (mediana) PARA CADA CORRIDA
    df_racing_laps['baseline_pace'] = df_racing_laps.groupby(group_cols)['lap_time_ms'].transform('median')

    # Mapear o ritmo base de volta para o DataFrame completo
    df_out = df_out.merge(df_racing_laps[['baseline_pace']], left_index=True, right_index=True, how='left')

    # Valor que vou usar como corte:
    df_out['baseline_pace_plus_threshold'] = df_out['baseline_pace'] * threshold_percent

    # 5. Identificar se o piloto perdeu posições na volta seguinte
    # Isso ajuda a diferenciar uma volta lenta por SC de uma rodada/erro individual.
    # Agrupamos por corrida e piloto para fazer o shift corretamente.
    driver_group_cols = group_cols + ['driver_full_name']
    df_out['next_lap_position'] = df_out.groupby(driver_group_cols)['position_on_lap'].shift(-1)
    # A condição é verdadeira se a posição piorou (ex: de P5 para P8)
    lost_position = df_out['next_lap_position'] > df_out['position_on_lap'] + 3 # Coloco uma tolerância de 3 posições aqui (a ideia é que, se o piloto cometeu um erro grave que o fez perder muito tempo, ele vai perder masi do que isso em posições)

    # 6. Identificar as voltas candidatas a SC (significativamente mais lentas)
    is_slow_lap = df_out['lap_time_ms'] > df_out['baseline_pace_plus_threshold']

    # 7. Uma volta é considerada de SC se for lenta E o piloto NÃO perdeu posição.
    # Isso filtra os erros individuais. Pq se for lento, e o piloto perdeu posições, então entendemos que ele pode ter errado e, nesse caso, a volta é mantida
    is_sc_lap = is_slow_lap & ~lost_position

    # 8. Identificar a volta ANTERIOR à volta de SC, por corrida
    # Usamos groupby + shift para "olhar" para a volta seguinte dentro de cada grupo de corrida
    is_lap_before_sc = df_out.assign(_is_sc_lap=is_sc_lap).groupby(group_cols)['_is_sc_lap'].shift(-1).fillna(False)

    # 9. A volta é considerada de SC se for a volta lenta (filtrada) OU a volta anterior a ela
    df_out['is_safety_car_lap'] = is_sc_lap | is_lap_before_sc

    # Limpeza final
    df_out = df_out.drop(columns=['baseline_pace', 'next_lap_position'], errors='ignore')
    df_out['is_safety_car_lap'] = df_out['is_safety_car_lap'].fillna(False) # Garante que não haja NaNs

    return df_out

def remove_invalid_laps(
    df: pd.DataFrame,
    remove_pit_laps: bool = True,
    remove_first_lap: bool = True,
    remove_sc_laps: bool = True,
    remove_dnf_races: bool = True
) -> pd.DataFrame:
    """
    Filters laps that are not representative of race pace under normal conditions.

    The function can remove:
    1. Pit stop in/out laps (requires 'is_pit_lap' column).
    2. The first lap of the race.
    3. Safety Car laps (calculated internally).
    4. Laps from races where the driver did not finish (DNF).

    This function does NOT remove statistical outliers (like slow laps due to driver errors),
    making it ideal for consistency analysis.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with lap times. Must contain 'lap_time_ms' and 'lap_number'.
        If `remove_pit_laps` is True, must also contain 'is_pit_lap'.
    remove_pit_laps : bool, default True
        If True, removes pit stop laps.
    remove_first_lap : bool, default True
        If True, removes the first lap of each race.
    remove_sc_laps : bool, default True
        If True, identifies and removes Safety Car laps.
    remove_dnf_races : bool, default True
        If True, removes all laps from races the driver did not finish ('Finished').

    Returns
    -------
    pd.DataFrame
        DataFrame with filtered lap times.
    """
    df_filtrado = df.copy()

    if remove_sc_laps:
        df_filtrado = _identify_sc_laps(df_filtrado)
        df_filtrado = df_filtrado.query("is_safety_car_lap == False")

    if remove_pit_laps:
        if 'is_pit_lap' not in df_filtrado.columns:
            raise ValueError("The column 'is_pit_lap' is required to remove pit stop laps.")
        df_filtrado = df_filtrado.query("is_pit_lap == 0")

    if remove_first_lap:
        df_filtrado = df_filtrado.query("lap_number > 1")

    if remove_dnf_races:
        if 'race_status' not in df_filtrado.columns:
            raise ValueError("The column 'race_status' is required to remove DNF races.")
        df_filtrado = df_filtrado.query("race_status == 0") # 0 = Finished

    return df_filtrado
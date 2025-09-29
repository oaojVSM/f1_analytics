import pandas as pd

def filtrar_evento(
    df: pd.DataFrame,
    year: int,
    circuit: str,
    driver_fn: str | None = None,
) -> pd.DataFrame:
    """
    Filtra o DataFrame por ano, circuito e opcionalmente por piloto.

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame com dados de eventos.
    year : int
        Ano da corrida.
    circuit : str
        Nome do circuito.
    driver_fn : str | None, default None
        Nome do piloto (first name ou identificador). Se None, não filtra por piloto.

    Retorna
    -------
    pd.DataFrame
        DataFrame filtrado.
    """
    mask = (df["year"] == year) & (df["circuit_name"] == circuit)

    if driver_fn is not None:
        mask &= df["driver_full_name"] == driver_fn

    return df.loc[mask].copy()
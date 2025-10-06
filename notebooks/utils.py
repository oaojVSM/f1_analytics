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


# Calculando a idade na primeira corrida:

def calcula_idade(data_nascimento, data_evento):
    '''A partir de duas datas, calcula a idade em anos (considerando anos bissextos)'''
    return (data_evento - data_nascimento).days / 365.25

def gerar_dataset_primeiro_evento(df_events: pd.DataFrame, df_drivers: pd.DataFrame) -> pd.DataFrame:
    '''
    Função para gerar um dataset com o primeiro evento de cada piloto. Vou usar pra extrair a primeira corrida, por exemplo, mas também posso usar pra extrair a primeira vitória, o primeiro pódio, etc.
    Basta eu filtrar previamente o dataset de acordo com o evento desejado (ex: filtrar por finishing_position == 1 pra extrair a primeira vitória, etc).
    '''

    # Aqui crio um dataset com o primeiro evento de cada piloto:

    df_first = (
        df_events.sort_values("race_date")
        .groupby("driver_full_name")
        .first()
        .reset_index()
        .loc[:, ["driver_id", "driver_full_name", "race_name", "race_date", "year", "circuit_name", "circuit_country", "race_status", "finishing_position", "starting_position"]] # Colunas que eu julgo que possam ser úteis
    )

    # Adicionando a data de nascimento:

    df_first = pd.merge(
        df_first,
        df_drivers[["driver_id", "dob"]],
        on="driver_id",
        how="left",
    )

    # Calculando a idade do piloto no evento:

    df_first['idade_primeira_corrida'] = df_first.apply(lambda row: calcula_idade(row['dob'], row['race_date']), axis=1)

    # Analisando o dataset, percebi que existem alguns pilotos muito jovens lá pros anos 60 que constam na base mas nunca largaram de fato (eles tem o status "Withdrew" e vou remover essas entradas)
    df_first = df_first[df_first['race_status'] != 'Withdrew']

    return df_first
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from dateutil.relativedelta import relativedelta
from matplotlib.patches import Rectangle
from typing import Optional, Tuple, List
import os


def filtrar_evento(
    df: pd.DataFrame,
    year: Optional[int] = None,
    race_name: Optional[str] = None,
    circuit_name: Optional[str] = None,
    driver_full_name: Optional[str] = None,
) -> pd.DataFrame:
    """
    Filtra o DataFrame de eventos com base nos critérios fornecidos.

    A função aplica filtros apenas para os argumentos que não são None,
    permitindo uma filtragem modular.

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame com dados de eventos.
    year : int, optional
        Ano da corrida.
    race_name : str, optional
        Nome da corrida.
    circuit_name : str, optional
        Nome do circuito.
    driver_full_name : str, optional
        Nome completo do piloto.

    Retorna
    -------
    pd.DataFrame
        DataFrame filtrado.
    """
    df_filtrado = df.copy()

    if year is not None:
        df_filtrado = df_filtrado[df_filtrado["year"] == year]

    if race_name is not None:
        df_filtrado = df_filtrado[df_filtrado["race_name"] == race_name]

    if circuit_name is not None:
        df_filtrado = df_filtrado[df_filtrado["circuit_name"] == circuit_name]

    if driver_full_name is not None:
        df_filtrado = df_filtrado[df_filtrado["driver_full_name"] == driver_full_name]

    return df_filtrado


def add_lap_time_ms_column(df: pd.DataFrame, lap_time_col: str = 'lap_time') -> pd.DataFrame:
    """
    Converte uma coluna de tempo de volta (string) para milissegundos e a adiciona ao DataFrame.

    A função lida com formatos como 'HH:MM:SS.ms' ou 'MM:SS.ms' e cria uma
    nova coluna chamada 'lap_time_ms'.

    Parâmetros
    ----------
    df : pd.DataFrame
        O DataFrame que contém a coluna de tempo de volta.

    Retorna
    -------
    pd.DataFrame
        O DataFrame com a nova coluna 'lap_time_ms'.
    """
    df_copy = df.copy()
    # pd.to_timedelta é vetorizado e lida com a série inteira de uma vez.
    # O `errors='coerce'` transforma valores inválidos em NaT (Not a Time),
    # que se tornarão NaN (Not a Number) após o cálculo.
    timedelta_series = pd.to_timedelta(df_copy[lap_time_col], errors='coerce')

    # Converte para milissegundos
    df_copy[f'{lap_time_col}_ms'] = timedelta_series.dt.total_seconds() * 1000

    return df_copy

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
        .loc[:, ["driver_id", "driver_full_name", "race_name", "race_date", "year", "circuit_name", "circuit_country", "race_status", "finishing_position", "starting_position", "race_count_for_driver"]] # Colunas que eu julgo que possam ser úteis
    )

    # Adicionando a data de nascimento:

    df_first = pd.merge(
        df_first,
        df_drivers[["driver_id", "dob"]],
        on="driver_id",
        how="left",
    )

    # Calculando a idade do piloto no evento:

    df_first['idade_primeiro_evento'] = df_first.apply(lambda row: calcula_idade(row['dob'], row['race_date']), axis=1)

    # Analisando o dataset, percebi que existem alguns pilotos muito jovens lá pros anos 60 que constam na base mas nunca largaram de fato (eles tem o status "Withdrew" e vou remover essas entradas)
    df_first = df_first[df_first['race_status'] != 'Withdrew']

    return df_first

def add_colunas_companheiro_equipe(
    df_dados: pd.DataFrame,
    metricas: list[str],
    df_lookup: pd.DataFrame = None,
    chaves_lookup: list[str] = ['round_id', 'driver_ref'],
    coluna_equipe: str = 'constructor_name',
    chaves_evento: list[str] = ['round_id'],
    colunas_id_tmate: list[str] = ['driver_ref']
) -> pd.DataFrame:
    """
    Adiciona colunas ao DataFrame com estatísticas do companheiro de equipe.

    Para cada linha/piloto no `df_dados`, esta função encontra o seu
    companheiro de equipe no mesmo evento, adiciona as `metricas`
    desse companheiro como novas colunas, e calcula a diferença entre elas.

    O DataFrame original é retornado com as colunas adicionadas. Nenhuma
    linha é filtrada ou removida.

    Notas:
    - Se um piloto não tiver companheiro de equipe, as novas colunas de
      companheiro terão valores nulos (NaN).
    - Se um piloto tiver múltiplos companheiros de equipe no mesmo evento,
      apenas as estatísticas do primeiro companheiro encontrado serão adicionadas.
    - A função assume que 'driver_ref' é a coluna que identifica unicamente um piloto.

    Argumentos:
        df_dados (pd.DataFrame): DataFrame principal com os dados dos pilotos.
        metricas (list[str]): Lista de nomes de colunas de métricas a serem
                              adicionadas para o companheiro de equipe.
        df_lookup (pd.DataFrame, optional): DataFrame para buscar a equipe do
                                             piloto. Se None, `df_dados` é
                                             usado. Default é None.
        chaves_lookup (list[str], optional): Colunas para o merge entre
                                             `df_dados` e `df_lookup`.
                                             Default é ['raceId', 'driver_ref'].
        coluna_equipe (str, optional): Nome da coluna que identifica a equipe.
                                       Default é 'constructorId'.
        chaves_evento (list[str], optional): Colunas que definem um evento único
                                             (ex: uma corrida).
                                             Default é ['raceId'].
        colunas_id_tmate (list[str], optional): Colunas de identificação do
                                                companheiro a serem adicionadas.
                                                'driver_ref' é obrigatório.
                                                Default é ['driver_ref'].

    Retorna:
        pd.DataFrame: Uma cópia do `df_dados` original com colunas adicionais
                      para as estatísticas do companheiro (sufixo '_tmate') e
                      a diferença entre as métricas (sufixo '_diff_tmate').
    """

    if 'driver_ref' not in colunas_id_tmate:
        raise ValueError("A coluna 'driver_ref' é obrigatória em `colunas_id_tmate`.")

    # --- Etapa 1: Garantir que temos a informação da equipe ---
    df_com_equipe = df_dados.copy()
    if coluna_equipe not in df_com_equipe.columns:
        source_df = df_lookup if df_lookup is not None else df_com_equipe

        colunas_info_equipe = chaves_lookup + [coluna_equipe]
        if not set(colunas_info_equipe).issubset(source_df.columns):
            raise ValueError(f"As chaves de lookup '{colunas_info_equipe}' não foram encontradas no df_lookup.")

        df_info_equipe = source_df[colunas_info_equipe].drop_duplicates()

        df_com_equipe = pd.merge(
            df_com_equipe,
            df_info_equipe,
            on=chaves_lookup,
            how='left'
        )

    # --- Etapa 2: Preparar dados do companheiro para o "self-merge" ---
    chaves_join = chaves_evento + [coluna_equipe]

    colunas_companheiro = chaves_join + colunas_id_tmate + metricas
    colunas_companheiro = sorted(list(set(colunas_companheiro)))

    if not set(colunas_companheiro).issubset(df_com_equipe.columns):
        colunas_faltantes = set(colunas_companheiro) - set(df_com_equipe.columns)
        raise ValueError(f"Colunas faltando no DataFrame: {colunas_faltantes}")

    df_companheiros = df_com_equipe[colunas_companheiro].copy()

    rename_map = {m: f"{m}_tmate" for m in metricas}
    for col in colunas_id_tmate:
        rename_map[col] = f"{col}_tmate"
    df_companheiros = df_companheiros.rename(columns=rename_map)

    # --- Etapa 3: Parear pilotos com seus companheiros ---
    df_pareado = pd.merge(
        df_com_equipe,
        df_companheiros,
        on=chaves_join,
        how='inner'  # Inner join para focar em equipes com > 1 piloto
    )

    # Remover comparações do piloto consigo mesmo
    df_pareado = df_pareado[df_pareado['driver_ref'] != df_pareado['driver_ref_tmate']]

    # --- Etapa 4: Preparar colunas do companheiro para o join final ---

    # Isolar as colunas do companheiro que queremos adicionar
    tmate_cols = [f"{m}_tmate" for m in metricas] + [f"{c}_tmate" for c in colunas_id_tmate]

    # Manter apenas uma entrada por piloto (em caso de múltiplos companheiros)
    df_stats_companheiro = df_pareado[chaves_lookup + tmate_cols].drop_duplicates(subset=chaves_lookup)

    # --- Etapa 5: Adicionar as colunas ao dataframe original ---
    df_final = pd.merge(
        df_dados,
        df_stats_companheiro,
        on=chaves_lookup,
        how='left'
    )

    # --- Etapa 6: Calcular a diferença para as métricas ---
    for m in metricas:
        col_tmate = f"{m}_tmate"
        col_diff = f"{m}_diff_tmate"
        
        if m in df_final.columns and col_tmate in df_final.columns:
            df_final[col_diff] = df_final[m] - df_final[col_tmate]

    return df_final

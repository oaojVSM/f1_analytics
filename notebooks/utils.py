import pandas as pd
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta

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

    df_first['idade_primeiro_evento'] = df_first.apply(lambda row: calcula_idade(row['dob'], row['race_date']), axis=1)

    # Analisando o dataset, percebi que existem alguns pilotos muito jovens lá pros anos 60 que constam na base mas nunca largaram de fato (eles tem o status "Withdrew" e vou remover essas entradas)
    df_first = df_first[df_first['race_status'] != 'Withdrew']

    return df_first

def gera_graf_top_10_mais_jovens(df_top_10_jovens: pd.DataFrame, titulo: str, xlabel: str, nome_a_ser_destacado: str):
    '''
    Função para gerar o gráfico dos 10 pilotos mais jovens a realizar X em alguma corrida na F1, basta inserir um dataset com o top 10.
    '''
    # Cria rótulo de idade em anos e dias
    df_top_10_jovens["idade_texto"] = df_top_10_jovens.apply(
        lambda r: f"{relativedelta(r['race_date'], r['dob']).years} anos e {relativedelta(r['race_date'], r['dob']).days} dias",
        axis=1
    )

    # Nome formatado para o eixo y
    df_top_10_jovens["label_y"] = (
        df_top_10_jovens["driver_full_name"] 
        + " (" 
        + df_top_10_jovens["year"].astype(str) 
        + " · " 
        + df_top_10_jovens["race_name"] 
        + ")"
    )

    # Plot
    fig, ax = plt.subplots(figsize=(18,9))

    bars = ax.barh(
        df_top_10_jovens["label_y"], 
        df_top_10_jovens["idade_primeiro_evento"], 
        color="#4C72B0"
    )

    # Destaque pro Verstappen
    for bar, name in zip(bars, df_top_10_jovens["driver_full_name"]):
        if nome_a_ser_destacado in name:
            bar.set_color("#FF7009")
            bar.set_linewidth(2)
            bar.set_edgecolor("black")

    # Rótulos de idade ao lado das barras
    for bar, label in zip(bars, df_top_10_jovens["idade_texto"]):
        ax.text(
            bar.get_width() + 0.05,
            bar.get_y() + bar.get_height()/2,
            label,
            va="center", ha="left", fontsize=10
        )

    # Ajustes visuais
    ax.set_xlim(0, df_top_10_jovens["idade_primeiro_evento"].max() * 1.15)
    ax.set_title(titulo, fontsize=16, pad=10)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("")
    ax.invert_yaxis()
    ax.grid(axis="x", linestyle="--", alpha=0.4)


    plt.tight_layout()
    plt.show()
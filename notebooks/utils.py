import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from dateutil.relativedelta import relativedelta
from matplotlib.patches import Rectangle
from typing import Optional, Tuple

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

def graf_top10_pilotos(
    df: pd.DataFrame,
    col_nome: str = "driver_full_name",
    col_valor: str = "qtd",
    col_detalhe: Optional[str] = None,   # ex.: "2016–2024"
    titulo: str = "Top 10 pilotos",
    xlabel: str = "Total",
    nome_a_destacar: str = "Verstappen",
    orientation: str = "horizontal",     # "horizontal" (barras) ou "vertical" (colunas)
    figsize: Tuple[int, int] = (18, 9),
    cor_base: str = "#4C72B0",
    cor_destaque: str = "#FF7009",
    mostrar_chips: bool = True,
    valor_format_str: str = "{:,.0f}"
):
    """
    Plota Top 10 pilotos (poles, vitórias, etc.) com visual consistente e destaque.
    - Sem subtítulo e sem nota de rodapé (menos “firula”).
    - Chips de rank ajustados para não sobrepor o nome.
    - orientation="vertical" produz colunas em pé.
    """
    # A formatação de número padrão substitui vírgula por ponto para o padrão brasileiro.

    # --- Dados ---
    dplot = df.copy().head(10).reset_index(drop=True)
    if col_detalhe and col_detalhe in dplot.columns:
        labels = dplot[col_nome] + "  (" + dplot[col_detalhe].astype(str) + ")"
    else:
        labels = dplot[col_nome]

    valores = dplot[col_valor].astype(float)
    nomes = dplot[col_nome]

    fig, ax = plt.subplots(figsize=figsize)

    # --- Fundo suave (cartão) ---
    ax.add_patch(Rectangle(
        (-0.02, -0.05), 1.04, 1.10,
        transform=ax.transAxes,
        facecolor="#f6f8fb", edgecolor="none", zorder=0
    ))

    # --- Plot (duas orientações) ---
    if orientation.lower().startswith("h"):
        # Horizontal (barh)
        y_pos = range(len(dplot))
        bars = ax.barh(
            y=list(y_pos),
            width=valores,
            color=cor_base,
            alpha=0.95,
            edgecolor="none",
            height=0.6,
            zorder=2,
        )

        # Destaque
        nome_lower = nome_a_destacar.lower()
        vmax = float(valores.max()) if len(valores) else 1.0
        for i, (bar, nome) in enumerate(zip(bars, nomes)):
            if nome_lower in str(nome).lower():
                bar.set_color(cor_destaque)
                bar.set_alpha(1.0)
                bar.set_linewidth(1.5)
                bar.set_edgecolor("black")
                ax.add_patch(Rectangle(
                    (0, bar.get_y()-0.08),
                    vmax*1.02,
                    bar.get_height()+0.16,
                    facecolor=cor_destaque, alpha=0.06, edgecolor="none", zorder=1
                ))

        # Eixo Y + labels
        ax.set_yticks(list(y_pos))
        ax.set_yticklabels([str(lbl) for lbl in labels])
        ax.invert_yaxis()  # #1 no topo

        # Espaçamento: aumenta margem à esquerda para caber chip
        plt.subplots_adjust(left=0.28)

        # Chips de rank (à ESQUERDA do eixo, sem overlap)
        if mostrar_chips:
            # “empurra” os rótulos um pouco para a direita
            ax.tick_params(axis='y', which='major', pad=6)
            # usa coordenadas de eixo para posicionar do lado de fora
            for i in y_pos:
                ax.text(
                    -0.02, i, f"#{i+1}",
                    transform=ax.get_yaxis_transform(),  # x em coords de eixo, y em dados (ticks)
                    va="center", ha="right",
                    fontsize=11, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#d0d7de"),
                    zorder=3
                )

        # Valores na ponta da barra
        for bar, val in zip(bars, valores):
            ax.text(
                bar.get_width() + (0.01 * vmax if vmax > 0 else 0.2),
                bar.get_y() + bar.get_height()/2,
                valor_format_str.format(val).replace(",", "."),
                va="center", ha="left", fontsize=11, zorder=3
            )

        # Estética
        ax.set_xlim(0, vmax * 1.15)
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel("")
        ax.grid(axis="x", linestyle="--", alpha=0.35)
        for spine in ["top", "right", "left"]:
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color("#d0d7de")

    else:
        # Vertical (colunas)
        x_pos = range(len(dplot))
        bars = ax.bar(
            x=list(x_pos),
            height=valores,
            color=cor_base,
            alpha=0.95,
            edgecolor="none",
            width=0.6,
            zorder=2,
        )

        nome_lower = nome_a_destacar.lower()
        vmax = float(valores.max()) if len(valores) else 1.0
        for i, (bar, nome) in enumerate(zip(bars, nomes)):
            if nome_lower in str(nome).lower():
                bar.set_color(cor_destaque)
                bar.set_alpha(1.0)
                bar.set_linewidth(1.5)
                bar.set_edgecolor("black")
                ax.add_patch(Rectangle(
                    (bar.get_x()-0.08, 0),
                    bar.get_width()+0.16,
                    vmax*1.02,
                    facecolor=cor_destaque, alpha=0.06, edgecolor="none", zorder=1
                ))

        # Rótulos no eixo X (rotacionados) e espaço
        ax.set_xticks(list(x_pos))
        ax.set_xticklabels([str(lbl) for lbl in labels], rotation=20, ha="right")
        plt.subplots_adjust(bottom=0.26)

        # Chips de rank (ACIMA de cada coluna)
        if mostrar_chips:
            for i, bar in enumerate(bars):
                ax.text(
                    bar.get_x() + bar.get_width()/2,
                    bar.get_height() + vmax*0.03,
                    f"#{i+1}",
                    ha="center", va="bottom",
                    fontsize=10, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#d0d7de"),
                    zorder=3
                )

        # Valores acima das colunas
        for bar, val in zip(bars, valores):
            ax.text(
                bar.get_x() + bar.get_width()/2,
                bar.get_height() + vmax*0.01,
                valor_format_str.format(val).replace(",", "."),
                ha="center", va="bottom", fontsize=11, zorder=3
            )

        # Estética
        ax.set_ylim(0, vmax * 1.20)  # um pouco mais de espaço p/ chips & valores
        ax.set_ylabel(xlabel, fontsize=12)
        ax.set_xlabel("")
        ax.grid(axis="y", linestyle="--", alpha=0.35)
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
        ax.spines["left"].set_color("#d0d7de")
        ax.spines["bottom"].set_color("#d0d7de")

    # Título enxuto
    ax.set_title(titulo, fontsize=18, pad=8, loc="left")

    plt.tight_layout()
    plt.show()


def identificar_voltas_safety_car(
    df_laps: pd.DataFrame,
    threshold_percent: float = 1.07,
    group_cols = ['year', 'race_name']
) -> pd.DataFrame:
    """
    Identifica prováveis voltas de Safety Car (ou VSC) em um DataFrame com múltiplas corridas.

    A lógica se baseia no fato de que, durante um SC, os tempos de volta de todos
    os pilotos aumentam significativamente. A função calcula um ritmo de corrida base
    para cada corrida e sinaliza as voltas cujo tempo mediano é muito superior a esse ritmo.

    Parâmetros
    ----------
    df_laps : pd.DataFrame
        DataFrame contendo os tempos de volta de uma ou mais corridas.
        Deve conter as colunas 'lap_number', 'lap_time_ms', 'is_pit_lap'.
    threshold_percent : float, default 1.07
        O percentual acima do ritmo base para considerar uma volta como de SC.
        Por exemplo, 1.07 significa que a mediana da volta deve ser 7% mais lenta
        que a mediana da corrida.

    Retorna
    -------
    pd.DataFrame
        Uma cópia do DataFrame original com a nova coluna 'is_safety_car_lap'.
    """
    df_out = df_laps.copy()

    # 1. Filtrar voltas que não representam ritmo de corrida (pit stops, 1ª volta)
    df_racing_laps = df_out.query("is_pit_lap == 0 and lap_number > 1").copy()

    # 2. Calcular o ritmo de corrida base (mediana) PARA CADA CORRIDA
    # O transform() alinha o resultado de volta ao DataFrame original.
    baseline_pace_per_race = df_racing_laps.groupby(group_cols)['lap_time_ms'].transform('median')

    # 3. Calcular a mediana do tempo de volta PARA CADA VOLTA de CADA CORRIDA
    #df_out['median_time_per_lap'] = df_out.groupby(group_cols + ['lap_number'])['lap_time_ms'].transform('median')

    # 4. Adicionar o ritmo base ao DataFrame de voltas de corrida para comparação
    df_racing_laps['baseline_pace'] = baseline_pace_per_race
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
    is_slow_lap = df_out['lap_time_ms'] > (df_out['baseline_pace'] * threshold_percent)

    # 7. Uma volta é considerada de SC se for lenta E o piloto NÃO perdeu posição.
    # Isso filtra os erros individuais.
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


def filtrar_voltas_para_analise(
    df: pd.DataFrame,
    remove_pit_laps: bool = True,
    remove_first_lap: bool = True,
    remove_sc_laps: bool = True,
    remove_dnf_races: bool = True
) -> pd.DataFrame:
    """
    Filtra voltas que não são representativas do ritmo de corrida em condições normais.

    A função pode remover:
    1. Voltas de entrada e saída de pit stops (requer a coluna 'is_pit_lap').
    2. A primeira volta da corrida.

    Esta função NÃO remove outliers estatísticos (como voltas lentas por erros do
    piloto), sendo ideal para análises de consistência.

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame com tempos de volta. Deve conter 'lap_time_ms' e 'lap_number'.
        Se `remove_pit_laps` for True, deve conter também 'is_pit_lap'.
    remove_pit_laps : bool, default True
        Se True, remove voltas de pit stop.
    remove_first_lap : bool, default True
        Se True, remove a primeira volta de cada corrida.
    remove_dnf_races : bool, default True
        Se True, remove todas as voltas de corridas que o piloto não terminou ('Finished').

    Retorna
    -------
    pd.DataFrame
        DataFrame com os tempos de volta filtrados.
    """
    df_filtrado = df.copy()

    if remove_pit_laps:
        if 'is_pit_lap' not in df_filtrado.columns:
            raise ValueError("A coluna 'is_pit_lap' é necessária para remover voltas de pit stop.")
        df_filtrado = df_filtrado.query("is_pit_lap == 0")

    if remove_first_lap:
        df_filtrado = df_filtrado.query("lap_number > 1")

    if remove_sc_laps:
        df_filtrado = df_filtrado.query("is_safety_car_lap == 0")

    if remove_dnf_races:
        if 'race_status' not in df_filtrado.columns:
            raise ValueError("A coluna 'race_status' é necessária para remover corridas não finalizadas (DNF).")
        df_filtrado = df_filtrado.query("race_status == 'Finished'")

    return df_filtrado

def comparar_consistencia_pilotos_hist(
    df_consistencia: pd.DataFrame,
    piloto_base: str = "Max Verstappen",
    pilotos_a_comparar: list = [],
    metrica: str = 'lap_time_std',
    bins: int = 50,
    figsize: tuple = (14, 7)
):
    """
    Gera histogramas comparando a consistência de um piloto base com outros pilotos.

    Para cada piloto na lista `pilotos_a_comparar`, um novo gráfico é gerado
    mostrando a distribuição da métrica de consistência (ex: 'lap_time_std')
    do piloto base vs. o piloto comparado.

    Parâmetros
    ----------
    df_consistencia : pd.DataFrame
        DataFrame gerado por `calcular_consistencia_pilotos`.
    piloto_base : str, default "Max Verstappen"
        O piloto principal para a comparação.
    pilotos_a_comparar : list
        Lista de nomes de pilotos para comparar com o piloto base.
    metrica : str, default 'lap_time_std'
        A coluna da métrica a ser plotada ('lap_time_std' ou 'consistency_cv').
    bins : int, default 50
        Número de bins para o histograma.
    figsize : tuple, default (14, 7)
        Tamanho da figura do gráfico.
    """
    if not pilotos_a_comparar:
        print("A lista `pilotos_a_comparar` está vazia. Nenhum gráfico para gerar.")
        return

    for piloto_comparado in pilotos_a_comparar:
        fig, ax = plt.subplots(figsize=figsize)

        pilotos_no_grafico = [piloto_base, piloto_comparado]
        df_plot = df_consistencia[df_consistencia['driver_full_name'].isin(pilotos_no_grafico)]

        # Define uma paleta de cores fixa para garantir consistência
        cor_base = "#FF7009"      # Laranja para o piloto base (Verstappen)
        cor_comparado = "#4C72B0" # Azul para o piloto comparado
        palette = {piloto_base: cor_base, piloto_comparado: cor_comparado}

        # Garante a ordem dos pilotos no gráfico e na legenda
        hue_order = [piloto_base, piloto_comparado]

        # Calcula o número de corridas (amostra) para cada piloto
        n_corridas_base = len(df_plot[df_plot['driver_full_name'] == piloto_base])
        n_corridas_comparado = len(df_plot[df_plot['driver_full_name'] == piloto_comparado])

        # Plot do histograma e da curva de densidade (KDE)
        sns.histplot(data=df_plot, x=metrica, hue='driver_full_name', bins=bins, kde=True, ax=ax, palette=palette, hue_order=hue_order)

        # Adiciona linhas verticais para a média de cada piloto
        media_base = df_plot[df_plot['driver_full_name'] == piloto_base][metrica].mean()
        media_comparado = df_plot[df_plot['driver_full_name'] == piloto_comparado][metrica].mean()

        ax.axvline(media_base, color=cor_base, linestyle='--', linewidth=2, label=f'Média {piloto_base.split(" ")[-1]}: {media_base:.2f}')
        ax.axvline(media_comparado, color=cor_comparado, linestyle='--', linewidth=2, label=f'Média {piloto_comparado.split(" ")[-1]}: {media_comparado:.2f}')

        # Títulos e rótulos
        ax.set_title(f"Comparativo de Consistência: {piloto_base} vs. {piloto_comparado}", fontsize=16)
        ax.set_xlabel(f"{metrica} (Menor é mais consistente)", fontsize=12)
        ax.set_ylabel("Frequência (nº de corridas)", fontsize=12)

        # Atualiza a legenda para incluir a contagem de corridas
        handles, _ = ax.get_legend_handles_labels()
        labels = [f'{piloto_base} ({n_corridas_base} corridas)', f'{piloto_comparado} ({n_corridas_comparado} corridas)'] + [h.get_label() for h in handles[2:]]
        ax.legend(handles=handles, labels=labels)

        ax.grid(axis='y', linestyle='--', alpha=0.6)
        plt.show()

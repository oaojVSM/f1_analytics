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

def graf_top_pilotos(
    df: pd.DataFrame,
    top_n: int = 10,
    col_nome: str = "driver_full_name",
    col_valor: str = "qtd",
    col_detalhe: Optional[str] = None,  # ex.: "2016–2024"
    titulo: Optional[str] = None,
    xlabel: str = "Total",
    nome_a_destacar: str = "Verstappen",
    orientation: str = "horizontal",  # "horizontal" (barras) ou "vertical" (colunas)
    figsize: Tuple[int, int] = (18, 9),
    cor_base: str = "#4C72B0",
    cor_destaque: str = "#FF7009",
    valor_format_str: str = "{:,.0f}"
):
    """
    Plota Top N pilotos (poles, vitórias, etc.) com visual consistente e destaque.
    - Lida com valores positivos e negativos (Horizontal e Vertical).
    - Corrige sobreposição de nomes de pilotos (ticklabels) com barras negativas.
    - orientation="vertical" produz colunas em pé.
    """
    
    # --- Dados ---
    dplot = df.copy().sort_values(by=col_valor, ascending=False).head(top_n).reset_index(drop=True)
    if col_detalhe and col_detalhe in dplot.columns:
        labels = dplot[col_nome] + "  (" + dplot[col_detalhe].astype(str) + ")"
    else:
        labels = dplot[col_nome]

    valores = dplot[col_valor].astype(float)
    nomes = dplot[col_nome]
    v_min, v_max = valores.min(), valores.max()
    val_range = v_max - v_min if (v_max - v_min) != 0 else v_max
    if val_range == 0: val_range = abs(v_max) if v_max != 0 else 1 # Evita divisão por zero

    fig, ax = plt.subplots(figsize=figsize)

    # --- Fundo suave (cartão) ---
    ax.add_patch(Rectangle(
        (-0.02, -0.05), 1.04, 1.10,
        transform=ax.transAxes,
        facecolor="#f6f8fb", edgecolor="none", zorder=0
    ))

    # --- Plot (duas orientações) ---
    if orientation.lower().startswith("h"):
        # =======================================================
        # GRÁFICO HORIZONTAL
        # =======================================================
        y_pos = range(len(dplot))
        bars = ax.barh(
            y=list(y_pos), width=valores, color=cor_base,
            alpha=0.95, edgecolor="none", height=0.6, zorder=2,
        )
        
        xlim_min, xlim_max = (v_min * 1.15, v_max * 1.15)
        if v_min >= 0: xlim_min = 0
        if v_max <= 0: xlim_max = 0
        highlight_xlim_min = xlim_min 

        # Destaque
        nome_lower = nome_a_destacar.lower()
        for i, (bar, nome) in enumerate(zip(bars, nomes)):
            if nome_lower in str(nome).lower():
                bar.set_color(cor_destaque)
                bar.set_alpha(1.0)
                bar.set_linewidth(1.5)
                bar.set_edgecolor("black")
                ax.add_patch(Rectangle(
                    (highlight_xlim_min, bar.get_y()-0.08), xlim_max - highlight_xlim_min,
                    bar.get_height()+0.16,
                    facecolor=cor_destaque, alpha=0.06, edgecolor="none", zorder=1
                ))
        
        # Posição dos Ticks (sem labels ainda)
        ax.set_yticks(list(y_pos))
        ax.invert_yaxis()  # #1 no topo

        # Valores (números) na ponta da barra
        for bar, val in zip(bars, valores):
            ha = 'left' if val >= 0 else 'right'
            offset_text = val_range * 0.01 
            x_pos = bar.get_width() + offset_text if val >= 0 else bar.get_width() - offset_text
            if val == 0:
                x_pos = offset_text
                ha = 'left'
            ax.text(
                x_pos, bar.get_y() + bar.get_height()/2,
                valor_format_str.format(val).replace(",", "."),
                va="center", ha=ha, fontsize=11, zorder=3
            )
        
        # Estética
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel("")
        ax.grid(axis="x", linestyle="--", alpha=0.35)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_color("#d0d7de")
        
        # --- CORREÇÃO HORIZONTAL ---
        # Define os limites do eixo X primeiro
        ax.set_xlim(xlim_min, xlim_max)

        if v_min < 0:
            # Move o eixo Y (spine) para o zero para separar barras positivas e negativas
            ax.spines["left"].set_position("zero")
            ax.spines["left"].set_color("#d0d7de")
            
            # Desliga os labels automáticos que ficariam sobrepostos no eixo
            ax.set_yticklabels([]) 
            
            # Usa um transform para posicionar os labels fora da área de dados
            trans = ax.get_yaxis_transform()
            for y, label_text in zip(y_pos, labels):
                # Posiciona o texto em coordenadas de eixo (X) e dados (Y)
                # -0.01 significa 1% à esquerda da área de plotagem
                ax.text(
                    -0.03, y, str(label_text) + " ", # Espaço para padding
                    transform=trans,
                    ha='right',  # Alinha o final do texto à posição
                    va='center', 
                    fontsize=11
                )
        else:
            # Comportamento original para valores apenas positivos
            ax.spines["left"].set_visible(False)
            ax.set_yticklabels([str(lbl) for lbl in labels]) # Nomes no lugar padrão

    else:
        # =======================================================
        # GRÁFICO VERTICAL
        # =======================================================
        x_pos = range(len(dplot))
        bars = ax.bar(
            x=list(x_pos), height=valores, color=cor_base,
            alpha=0.95, edgecolor="none", width=0.6, zorder=2,
        )

        ylim_min, ylim_max = (v_min * 1.2, v_max * 1.2)
        if v_min >= 0: ylim_min = 0
        if v_max <= 0: ylim_max = 0
        ax.set_ylim(ylim_min, ylim_max)

        # Destaque
        nome_lower = nome_a_destacar.lower()
        for i, (bar, nome) in enumerate(zip(bars, nomes)):
            if nome_lower in str(nome).lower():
                bar.set_color(cor_destaque)
                bar.set_alpha(1.0)
                bar.set_linewidth(1.5)
                bar.set_edgecolor("black")
                ax.add_patch(Rectangle(
                    (bar.get_x()-0.08, ylim_min), bar.get_width()+0.16,
                    ylim_max - ylim_min,
                    facecolor=cor_destaque, alpha=0.06, edgecolor="none", zorder=1
                ))

        # Valores (números) acima/abaixo das colunas
        for bar, val in zip(bars, valores):
            va = 'bottom' if val >= 0 else 'top'
            offset = val_range * 0.01
            y_pos = bar.get_height() + offset if val >= 0 else bar.get_height() - offset
            if val == 0:
                y_pos = offset
                va = 'bottom'
            ax.text(
                bar.get_x() + bar.get_width()/2, y_pos,
                valor_format_str.format(val).replace(",", "."),
                ha="center", va=va, fontsize=11, zorder=3
            )

        # Estética
        ax.set_ylabel(xlabel, fontsize=12)
        ax.set_xlabel("")
        ax.grid(axis="y", linestyle="--", alpha=0.35)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#d0d7de")
        
        # Define a posição dos ticks (sem labels ainda)
        ax.set_xticks(list(x_pos))

        # --- CORREÇÃO VERTICAL ---
        if v_min < 0:
            # Move o eixo X (spine) para o zero
            ax.spines["bottom"].set_position("zero")
            ax.spines["bottom"].set_color("#d0d7de")
            
            # Move os Ticks e os Nomes (ticklabels) para o TOPO
            ax.xaxis.set_ticks_position("top")
            ax.spines["top"].set_visible(False) 
            
            # Aplica os Nomes (labels) com alinhamento e rotação para o TOPO
            ax.set_xticklabels(
                [str(lbl) for lbl in labels], 
                rotation=20, 
                ha="left"  # Alinha o *começo* do nome no tick (para "fora")
            )
            
        else:
            # Comportamento original (sem negativos)
            ax.spines["bottom"].set_color("#d0d7de")
            ax.spines["top"].set_visible(False)
            
            # Ticks e Nomes EMBAIXO (padrão)
            ax.xaxis.set_ticks_position("bottom") 
            ax.set_xticklabels(
                [str(lbl) for lbl in labels], 
                rotation=20, 
                ha="right" # Alinha o *fim* do nome no tick (para "fora")
            )

    # Título
    final_titulo = titulo if titulo is not None else f"Top {top_n} pilotos"
    ax.set_title(final_titulo, fontsize=18, pad=8, loc="left")
    
    # Ajuste final de layout
    plt.tight_layout()
    
    # Ajuste de margem pós-tight_layout (necessário para nomes rotacionados)
    if not orientation.lower().startswith("h"): # Se for Vertical
        try:
            max_label_len = max([len(str(l)) for l in labels])
        except ValueError:
            max_label_len = 0
        
        # Heurística para margem
        margin_needed = max(0.15, min(0.4, max_label_len * 0.015)) 
        
        if v_min < 0:
            # Deixa espaço no TOPO para os nomes
            fig.subplots_adjust(top=1.0 - margin_needed) 
        else:
            # Deixa espaço EMBAIXO para os nomes
            fig.subplots_adjust(bottom=margin_needed) 

    plt.show()

    
def identificar_voltas_safety_car(
    df_laps: pd.DataFrame,
    threshold_percent: float = 1.20,
    group_cols = ['year', 'race_name']
) -> pd.DataFrame:
    """
    Identifica prováveis voltas de Safety Car (ou VSC) em um DataFrame com múltiplas corridas.

    A lógica se baseia no fato de que, durante um SC, os tempos de volta de todos
    os pilotos aumentam significativamente. A função calcula um ritmo de corrida base
    para cada corrida e sinaliza as voltas cujo tempo mediano é muito superior a esse ritmo.
    Também é feita uma verificação se o piloto perdeu posições na volta seguinte, sendo que a lógica é
    se ele perdeu posições, então pode ter cometido um erro próprio, então essa volta é mantida no dataset.

    Originalmente, fiz essa função analisando mediana geral da volta VS mediana geral da corrida, mas não funciona
    eu acabo carregando muitas voltas que não fazem sentido, o único jeito que a análise ficou consistente foi
    pegando a mediana da corrida e comparando com a volta de cada piloto e fazendo a verificação de perda de posições

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
        df_filtrado = df_filtrado.query("is_safety_car_lap == False")

    if remove_dnf_races:
        if 'race_status' not in df_filtrado.columns:
            raise ValueError("A coluna 'race_status' é necessária para remover corridas não finalizadas (DNF).")
        df_filtrado = df_filtrado.query("race_status == 0") # 0 = Finished

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


def get_final_quali_session(
    df_quali_all: pd.DataFrame,
    col_event: str = 'round_id',
    col_driver: str = 'driver_id',
    col_session: str = 'session_type',
    col_pos: str = 'position'
) -> pd.DataFrame:
    """
    Filtra um DataFrame de resultados de qualificação (Q1, Q2, Q3)
    para retornar APENAS a posição final de cada piloto em cada evento.

    A posição final é definida pelo resultado no segmento mais alto (Q3 > Q2 > Q1)
    que o piloto alcançou.

    Parâmetros:
    ----------
    df_quali_all : pd.DataFrame
        O DataFrame de entrada contendo *todos* os resultados (Q1, Q2, Q3, etc.).
    col_event : str, opcional
        Nome da coluna que identifica o evento (ex: 'round_id').
    col_driver : str, opcional
        Nome da coluna que identifica o piloto (ex: 'driverId').
    col_session : str, opcional
        Nome da coluna com os tipos de sessão (ex: 'session_type').
    col_pos : str, opcional
        Nome da coluna com a posição (ex: 'position').

    Retorna:
    -------
    pd.DataFrame
        Um DataFrame filtrado contendo uma linha por piloto/evento,
        com sua posição final de qualificação.
    """
    
    # Copia para evitar SettingWithCopyWarning
    df_proc = df_quali_all.copy()

    # --- Passo 1: Mapear a Prioridade dos Segmentos ---
    # Define qual sessão tem prioridade (Q3 é a mais alta)
    priority_map = {
        'Q1': 1,
        'Q2': 2,
        'Q3': 3,
    }

    # Cria a coluna de prioridade
    df_proc['segment_priority'] = df_proc[col_session].map(priority_map)
    
    # Remove linhas que não são de qualificação (ex: FP1, 'R')
    df_proc = df_proc[df_proc['segment_priority'].notna()].copy()

    # --- Passo 2: Encontrar o Índice (idx) da Posição Final ---
    
    # Agrupa por evento e piloto
    groups = df_proc.groupby([col_event, col_driver])
    
    try:
        idx_final_position = groups['segment_priority'].idxmax()
    except ValueError as e:
        print(f"Aviso: Não foi possível processar os grupos. {e}")
        # Retorna um DataFrame vazio se não houver dados de quali válidos
        return pd.DataFrame(columns=df_quali_all.columns)

    # --- Passo 3: Selecionar as Linhas Finais ---
    # Usa .loc[] para selecionar apenas as linhas com os índices que encontramos
    df_final_results = df_proc.loc[idx_final_position].copy()
    
    # --- Limpeza e Retorno ---
    # Remove a coluna temporária
    df_final_results = df_final_results.drop(columns=['segment_priority'])
    
    # Renomeia a coluna de posição para maior clareza (opcional)
    df_final_results = df_final_results.rename(columns={col_pos: 'final_quali_position'})

    return df_final_results
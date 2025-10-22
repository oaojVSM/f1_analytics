import pandas as pd
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta
from matplotlib.patches import Rectangle
from typing import Optional, Tuple

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

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pyparsing import Dict
import seaborn as sns
from dateutil.relativedelta import relativedelta
from matplotlib.patches import Rectangle, Circle
from typing import Optional, Tuple, List, Union, Dict
import os

# Define o caminho para o estilo do Matplotlib
# O estilo 'dark_theme.mplstyle' deve estar na mesma pasta que este script (utils.py)
style_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dark_theme.mplstyle')

# Verifica se o arquivo de estilo existe antes de tentar usá-lo
if os.path.exists(style_path):
    plt.style.use(style_path)
else:
    print(f"Aviso: Arquivo de estilo não encontrado em '{style_path}'. Usando o estilo padrão do Matplotlib.")


def graf_radar_padrao(
    dados: Dict[str, float],
    titulo: str = "Radar Chart",
    cor_base: str = "#FF7009",
    alpha_preenchimento: float = 0.2,
    center_value: float = None,
    center_value_fmt: str = "{:.1f}",
    figsize: Tuple[int, int] = (10, 10),
    save_fig: bool = False,
    save_path: str = 'grafs',
    label_fontsize: int = 14,
    max_val: float = None,  # Optional manual max value for scaling
    tip_value_fmt: str = "{:.0f}",
    tip_fontsize: int = 12,
    center_fontsize: int = 24
):
    """
    Plota um gráfico de radar limpo e estilizado.
    
    Args:
        dados: Dicionário onde as chaves são as categorias (stats) e os valores são os números.
    """
    # Preparação dos dados
    categories = list(dados.keys())
    values = list(dados.values())
    N = len(categories)
    
    # Repetir o primeiro valor para fechar o ciclo
    values += values[:1]
    
    # Calcular ângulos
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    
    # Criar figura
    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(projection='polar'))
    
    # Ajustar offset para que o primeiro eixo fique no topo e sentido horário
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    
    # Desenhar linhas e preenchimento
    ax.plot(angles, values, color=cor_base, linewidth=2, linestyle='solid')
    ax.fill(angles, values, color=cor_base, alpha=alpha_preenchimento)
    
    # Estilização dos Eixos (Categorias)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=label_fontsize)
    
    # Customizar os labels dos eixos para ficarem afastados (padding)
    for label, angle in zip(ax.get_xticklabels(), angles[:-1]):
        if angle in (0, np.pi):
            label.set_horizontalalignment('center')
        elif 0 < angle < np.pi:
            label.set_horizontalalignment('left')
        else:
            label.set_horizontalalignment('right')

    # Remover yticks padrão ou customizar
    ax.yaxis.grid(True, color='#444444', linestyle='dashed', alpha=0.5)
    ax.xaxis.grid(True, color='#444444', linestyle='dashed', alpha=0.5)
    
    # Remover labels radiais (números do eixo Y) para look "clean"
    ax.set_yticklabels([])
    
    # Definir limite máximo se fornecido, senão usa max dos dados
    if max_val:
        ax.set_ylim(0, max_val)
    else:
        ax.set_ylim(0, max(values) * 1.1)

    # Remover spine circular externa para visual mais limpo
    ax.spines['polar'].set_visible(False)
    
    # Adicionar Valores nas pontas
    for angle, value in zip(angles[:-1], values[:-1]):
        ax.text(angle, value + (max(values)*0.1 if not max_val else max_val*0.1), 
                tip_value_fmt.format(value), 
                ha='center', va='center', size=tip_fontsize, color='white', fontweight='bold')

    # Valor Central Opcional
    if center_value is not None:
        ax.text(0, 0, center_value_fmt.format(center_value), 
                ha='center', va='center', size=center_fontsize, fontweight='bold', color='white', zorder=10)

    # Título
    plt.title(titulo, size=20, y=1.05)
    
    plt.tight_layout()

    # Salvamento
    if save_fig:
        filename_base = "".join(c for c in titulo.lower() if c.isalnum() or c in (' ', '_')).replace(' ', '_')
        filename = f"{filename_base}_radar.png"
        
        os.makedirs(save_path, exist_ok=True)
        full_path = os.path.join(save_path, filename)
        
        try:
            fig.savefig(full_path, bbox_inches='tight', dpi=300)
            print(f"Gráfico salvo em: {os.path.abspath(full_path)}")
        except Exception as e:
            print(f"Erro ao salvar o gráfico: {e}")

    plt.show()




def gera_graf_top_10_mais_jovens(
    df_top_10_jovens: pd.DataFrame, 
    titulo: str, 
    xlabel: str, 
    nome_a_ser_destacado: str,
    save_fig: bool = False,
    save_path: str = 'grafs'
):
    '''
    Função para gerar o gráfico dos 10 pilotos mais jovens.
    '''
    
    # Função interna para calcular a idade correta em anos e dias
    def calcula_idade_texto_correto(row):
        rd = relativedelta(row['race_date'], row['dob'])
        anos = rd.years
        # Calcula a diferença em dias desde o último aniversário
        ultimo_aniversario = row['dob'] + relativedelta(years=anos)
        dias_restantes = (row['race_date'] - ultimo_aniversario).days
        return f"{anos} years and {dias_restantes} days"

    # Aplica a função de cálculo de idade correta
    df_top_10_jovens["idade_texto"] = df_top_10_jovens.apply(
        calcula_idade_texto_correto, 
        axis=1
    )

    df_top_10_jovens["label_y"] = (
        df_top_10_jovens["driver_full_name"] 
        + " (" 
        + df_top_10_jovens["year"].astype(str) 
        + " · " 
        + df_top_10_jovens["race_name"] 
        + ")"
    )

    fig, ax = plt.subplots(figsize=(18,9))

    bars = ax.barh(
        df_top_10_jovens["label_y"], 
        df_top_10_jovens["idade_primeiro_evento"]
    )

    for bar, name in zip(bars, df_top_10_jovens["driver_full_name"]):
        if nome_a_ser_destacado in name:
            bar.set_color("#FF7009")
            bar.set_linewidth(2)
            # Revertido para 'black' (seu original)
            bar.set_edgecolor("black") 

    for bar, label in zip(bars, df_top_10_jovens["idade_texto"]):
        ax.text(
            bar.get_width() + 0.05,
            bar.get_y() + bar.get_height()/2,
            label,
            va="center", ha="left"
            # Fontsize removido para obedecer o .mplstyle
        )

    ax.set_xlim(0, df_top_10_jovens["idade_primeiro_evento"].max() * 1.15)
    ax.set_title(titulo, pad=10) # Fontsize removido
    ax.set_xlabel(xlabel)
    ax.set_ylabel("")
    ax.invert_yaxis()
    # Grid removido para obedecer o .mplstyle

    if save_fig:
        filename_base = "".join(c for c in titulo.lower() if c.isalnum() or c in (' ', '_')).replace(' ', '_')
        filename = f"{filename_base}_safe.png"
        
        os.makedirs(save_path, exist_ok=True)
        
        full_path = os.path.join(save_path, filename)
        try:
            fig.savefig(full_path, bbox_inches='tight', pad_inches=0.1)
            print(f"Gráfico salvo em: {os.path.abspath(full_path)}")
        except Exception as e:
            print(f"Erro ao salvar o gráfico: {e}")

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
    figsize: Optional[Tuple[int, int]] = None,
    cor_base: Optional[str] = None,
    cor_destaque: str = "#FF7009",
    valor_format_str: str = "{:,.0f}",
    save_fig: bool = False,
    save_path: str = 'grafs'
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

    if figsize:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig, ax = plt.subplots()


    # --- Plot (duas orientações) ---
    if orientation.lower().startswith("h"):
        # =======================================================
        # GRÁFICO HORIZONTAL
        # =======================================================
        y_pos = range(len(dplot))
        bars = ax.barh(
            y=list(y_pos), width=valores, color=cor_base,
            height=0.6, zorder=2,
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
                va="center", ha=ha, zorder=3
            )
        
        # Estética
        ax.set_xlabel(xlabel)
        ax.set_ylabel("")
        ax.grid(axis="x")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        
        # --- CORREÇÃO HORIZONTAL ---
        # Define os limites do eixo X primeiro
        ax.set_xlim(xlim_min, xlim_max)

        if v_min < 0:
            # Move o eixo Y (spine) para o zero para separar barras positivas e negativas
            ax.spines["left"].set_position("zero")
            
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
                    va='center'
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
            width=0.6, zorder=2,
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
                ha="center", va=va, zorder=3
            )

        # Estética
        ax.set_ylabel(xlabel)
        ax.set_xlabel("")
        ax.grid(axis="y")
        ax.spines["right"].set_visible(False)
        
        # Define a posição dos ticks (sem labels ainda)
        ax.set_xticks(list(x_pos))

        # --- CORREÇÃO VERTICAL ---
        if v_min < 0:
            # Move o eixo X (spine) para o zero
            ax.spines["bottom"].set_position("zero")
            
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
    ax.set_title(final_titulo, pad=8, loc="left")
    
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


    if save_fig:
        # Sanitiza o título para um nome de arquivo válido
        filename_base = "".join(c for c in titulo.lower() if c.isalnum() or c in (' ', '_')).replace(' ', '_')
        filename = f"{filename_base}_safe.png"
        
        # Garante que o diretório de destino exista
        os.makedirs(save_path, exist_ok=True)
        
        full_path = os.path.join(save_path, filename)
        try:
            fig.savefig(full_path)
            print(f"Gráfico salvo em: {os.path.abspath(full_path)}")
        except Exception as e:
            print(f"Erro ao salvar o gráfico: {e}")


    plt.show()



def graf_barras_padrao(
    df_dados: pd.DataFrame,
    x_col: str,
    y_col: str,
    hue_col: Optional[str] = None,
    cores_map: Optional[Union[Dict, str]] = None,
    titulo: str = "Gráfico de Barras",
    xlabel: str = "Eixo X",
    ylabel: str = "Eixo Y",
    destaque: list = None,
    figsize: Optional[Tuple[int, int]] = (16, 9),
    save_fig: bool = False,
    save_path: str = 'grafs',
    titulo_legenda: str = None,
    fmt_rotulo: str = '%.0f',
    dodge: bool = False,
    barlabel_fontsize: int = 18,
    axislabel_fontsize: int = 18,
    title_fontsize: int = 18,
    tick_fontsize: int = 16,
    show_legend: bool = True,
):
    """
    fmt_rotulo : str
        String de formatação para os valores acima das barras.
        Exemplos: 
        '%.0f'   -> 10 (Inteiro)
        '%.2f'   -> 10.50 (2 casas decimais)
        '%.1f%%' -> 10.5% (Percentual, adiciona o símbolo %)
        'R$ %.0f' -> R$ 10 (Moeda)
    """
    
    # 1. Filtragem e Preparação dos Dados
    df_plot = df_dados.copy()

    # Filtro de destaque
    coluna_filtro = hue_col if hue_col else x_col
    if destaque and coluna_filtro in df_plot.columns:
        df_plot = df_plot[df_plot[coluna_filtro].isin(destaque)]

    # Lógica de cores inteligente (Substring matching)
    palette_to_use = cores_map
    if isinstance(cores_map, dict):
        col_color = hue_col if hue_col else x_col
        if col_color in df_plot.columns:
            unique_vals = df_plot[col_color].unique()
            palette_to_use = {}
            
            # Ordena chaves por tamanho para priorizar matches mais longos/específicos
            # Ex: "Oracle Red Bull" terá prioridade sobre "Red Bull"
            sorted_keys = sorted(cores_map.keys(), key=lambda k: len(str(k)), reverse=True)
            
            for val in unique_vals:
                val_str = str(val)
                # 1. Match exato (Prioridade máxima)
                if val in cores_map:
                    palette_to_use[val] = cores_map[val]
                    continue
                
                # 2. Substring match
                for key in sorted_keys:
                    if str(key) in val_str:
                        palette_to_use[val] = cores_map[key]
                        break

    # Cria a figura
    if figsize:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig, ax = plt.subplots()

    # 2. Plotagem
    sns.barplot(
        data=df_plot,
        x=x_col,
        y=y_col,
        hue=hue_col if hue_col else x_col,
        palette=palette_to_use,
        edgecolor='black',
        linewidth=1,
        ax=ax,
        dodge=dodge
    )

    # 3. Estilização
    ax.set_title(f"{titulo}", fontsize=title_fontsize, pad=20)
    ax.set_xlabel(xlabel, fontsize=axislabel_fontsize)
    ax.set_ylabel(ylabel, fontsize=axislabel_fontsize)
    
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.tick_params(axis='both', labelsize=tick_fontsize)
    plt.xticks(rotation=45, ha='right')

    # Legenda inteligente
    if show_legend and hue_col and hue_col != x_col:
        ax.legend(title=hue_col if titulo_legenda is None else titulo_legenda, bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)

    else:
        if ax.get_legend():
            ax.get_legend().remove()

    # Data Labels (Valores em cima das barras) com formatação customizada
    # Alterado para usar a variável fmt_rotulo
    for container in ax.containers:
        ax.bar_label(container, fmt=fmt_rotulo, padding=3, fontsize=barlabel_fontsize)

    plt.tight_layout()

    # 4. Salvamento
    if save_fig:
        base_name = titulo.lower().replace(' ', '_')
        filename_base = "".join(c for c in f'{base_name}'.lower() if c.isalnum() or c in (' ', '_')).replace(' ', '_')
        filename = f"{filename_base}_safe.png"
        
        os.makedirs(save_path, exist_ok=True)
        full_path = os.path.join(save_path, filename)
        
        try:
            fig.savefig(full_path, bbox_inches='tight', dpi=300)
            print(f"Gráfico salvo em: {os.path.abspath(full_path)}")
        except Exception as e:
            print(f"Erro ao salvar o gráfico: {e}")

    plt.show()
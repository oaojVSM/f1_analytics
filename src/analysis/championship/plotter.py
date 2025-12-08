import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from dateutil.relativedelta import relativedelta
from matplotlib.patches import Rectangle
from typing import Optional, Tuple, List
import os

# Define o caminho para o estilo do Matplotlib
# O estilo 'dark_theme.mplstyle' deve estar na mesma pasta que este script (utils.py)
style_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dark_theme.mplstyle')

# Verifica se o arquivo de estilo existe antes de tentar usá-lo
if os.path.exists(style_path):
    plt.style.use(style_path)
else:
    print(f"Aviso: Arquivo de estilo não encontrado em '{style_path}'. Usando o estilo padrão do Matplotlib.")

    

def plot_wcc(
    df_campeonato: pd.DataFrame,
    ano: int = 2025,
    times_destaque: list = None,
    figsize: Optional[Tuple[int, int]] = (16, 9),
    save_fig: bool = False,
    save_path: str = 'grafs'
):
    """
    Gera um gráfico de linha mostrando a evolução dos pontos do Campeonato de Construtores
    ao longo das rodadas (rounds), seguindo a estética definida pelo usuário.

    Parâmetros
    ----------
    df_campeonato : pd.DataFrame
        DataFrame resultante da query SQL de teamchampionship.
        Deve conter colunas: 'round_id', 'year', 'race_name', 'constructor_name', 'points'.
    ano : int
        O ano do campeonato a ser filtrado e plotado.
    times_destaque : list, opcional
        Lista de nomes de construtores para destacar (se None, plota todos coloridos).
        Útil se quiser focar apenas na briga McLaren vs Red Bull, por exemplo.
    figsize : tuple, default (16, 9)
        Tamanho da figura do gráfico.
    save_fig : bool, default False
        Se True, salva o gráfico no disco.
    save_path : str, default 'grafs'
        Caminho da pasta onde o arquivo será salvo.
    """
    
    # 1. Filtragem e Preparação dos Dados
    df_plot = df_campeonato[df_campeonato['year'] == ano].copy()
    
    if df_plot.empty:
        print(f"Nenhum dado encontrado para o ano {ano}.")
        return

    # Garante que os rounds estejam em ordem crescente (a query original estava DESC)
    df_plot.sort_values(by='round_id', ascending=True, inplace=True)

    # 2. Configuração Visual (Cores das Equipes)
    # Hex codes aproximados para a temporada 2024/2025
    cores_times = {
        'McLaren': '#FF8000',
        'Red Bull': '#0600EF',
        'Ferrari': '#DC0000',
        'Mercedes': '#00D2BE',
        'Aston Martin': '#006F62',
        'Alpine F1 Team': '#0090FF',
        'Williams': '#64C4FF',
        'RB F1 Team': '#6692FF', # Racing Bulls
        'Haas F1 Team': '#B6BABD',
        'Sauber': '#52E252'
    }

    # Se o usuário passou uma lista de destaques, filtramos ou acinzentamos os outros?
    # Neste design, vou filtrar para mostrar apenas os solicitados se a lista for passada,
    # senão mostra todos (padrão de evolução de campeonato).
    if times_destaque:
        df_plot = df_plot[df_plot['constructor_name'].isin(times_destaque)]
    
    # Cria a figura
    if figsize:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig, ax = plt.subplots()

    # 3. Plotagem
    # Usamos lineplot com markers para marcar cada GP
    sns.lineplot(
        data=df_plot,
        x='race_name',
        y='points',
        hue='constructor_name',
        palette=cores_times,
        marker='o', # Bolinha em cada corrida
        linewidth=2.5, # Linha um pouco mais grossa para visibilidade
        ax=ax
    )

    # 4. Estilização (Seguindo seu padrão)
    ax.set_title(f"Worlds Constructors Championship Points - {ano}", fontsize=16, pad=20)
    ax.set_xlabel("Grand Prix", fontsize=12)
    ax.set_ylabel("Points", fontsize=12)
    
    # Grid apenas no eixo Y como solicitado
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Rotacionar os nomes das corridas no eixo X para não encavalar
    plt.xticks(rotation=45, ha='right')

    # Ajuste da legenda
    # Move a legenda para fora se tiver muitos times, ou canto superior esquerdo
    ax.legend(title='Constructor', bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)

    # Ajuste de layout para caber a legenda e rotação do eixo X
    plt.tight_layout()

    # 5. Lógica de Salvamento (Sua lógica original)
    if save_fig:
        # Sanitiza o nome do arquivo
        nomes_times = "todos" if not times_destaque else "_".join(times_destaque)
        filename_base = "".join(c for c in f'evolucao_construtores_{ano}_{nomes_times}'.lower() if c.isalnum() or c in (' ', '_')).replace(' ', '_')
        filename = f"{filename_base}_safe.png"
        
        # Garante que o diretório existe
        os.makedirs(save_path, exist_ok=True)
        
        full_path = os.path.join(save_path, filename)
        try:
            fig.savefig(full_path, bbox_inches='tight', dpi=300) # dpi 300 para alta qualidade
            print(f"Gráfico salvo em: {os.path.abspath(full_path)}")
        except Exception as e:
            print(f"Erro ao salvar o gráfico: {e}")

    plt.show()

def plot_wdc(
    df_campeonato: pd.DataFrame,
    ano: int = 2025,
    pilotos_destaque: List[str] = None,
    figsize: Optional[Tuple[int, int]] = (16, 9),
    save_fig: bool = False,
    save_path: str = 'grafs'
):
    """
    Gera um gráfico de linha mostrando a evolução dos pontos do Campeonato de Pilotos
    ao longo das rodadas (rounds), focado nos protagonistas definidos.

    Parâmetros
    ----------
    df_campeonato : pd.DataFrame
        DataFrame resultante da query SQL de driverchampionship.
        Deve conter colunas: 'round_id', 'year', 'race_name', 'driver_full_name', 'points'.
    ano : int
        O ano do campeonato a ser filtrado.
    pilotos_destaque : list, opcional
        Lista de nomes COMPLETOS dos pilotos (ex: ['Lando Norris', 'Max Verstappen']).
        Se None, plota o Top 5 do campeonato final.
    figsize : tuple, default (16, 9)
        Tamanho da figura.
    save_fig : bool
        Se True, salva o gráfico.
    save_path : str
        Pasta de destino.
    """
    
    # 1. Preparação dos Dados
    df_plot = df_campeonato[df_campeonato['year'] == ano].copy()
    
    if df_plot.empty:
        print(f"Nenhum dado encontrado para o ano {ano}.")
        return

    # Garante ordem cronológica (a query original vem DESC)
    df_plot.sort_values(by='round_id', ascending=True, inplace=True)

    # 2. Filtragem de Pilotos
    # Se o usuário não passar lista, pegamos automaticamente os top 5 da última rodada
    if not pilotos_destaque:
        ultima_rodada = df_plot['round_id'].max()
        top_5 = df_plot[df_plot['round_id'] == ultima_rodada].sort_values('points', ascending=False).head(5)['driver_full_name'].tolist()
        pilotos_destaque = top_5
        print(f"No drivers specified. Plotting Top 5: {pilotos_destaque}")
    
    # Filtra o dataset apenas para os pilotos selecionados
    df_plot = df_plot[df_plot['driver_full_name'].isin(pilotos_destaque)]

    # 3. Mapeamento de Cores (Driver -> Team Color)
    # Hex codes atualizados para 2025 (Considerando Hamilton na Ferrari, etc, se for o caso)
    # Mapeando os principais protagonistas da sua narrativa
    cores_pilotos = {
# --- DISPUTA DO TÍTULO ---
        'Max Verstappen': '#0600EF',  # Azul Red Bull Oficial
        'Lando Norris':   '#FF8000',  # Laranja McLaren Oficial
        'Oscar Piastri':  '#FCD800',  # Amarelo (Diferenciação T-Cam/Capacete) - Alto contraste com Laranja
        
        # --- FERRARI (Hamilton vs Leclerc) ---
        'Charles Leclerc': '#DC0000', # Vermelho Ferrari Clássico
        'Lewis Hamilton':  '#E8E817', # Amarelo Neon (Cor assinatura do Lewis) ou #AF0000 (Vermelho Escuro)
        
        # --- MERCEDES ---
        'George Russell': '#00D2BE',  # Turquesa Mercedes
        'Andrea Kimi Antonelli': '#005A52', # Turquesa Escuro/Verde para diferenciar
        
        # --- OUTROS ---
        'Fernando Alonso': '#006F62', # Verde Aston Martin
        'Sergio Perez':    '#7878FF', # Azul mais claro/desbotado (simbólico, rs)
        'Carlos Sainz':    '#0090FF', # Azul Williams (supondo 2025 na Williams)
    }

    # Cria a figura
    if figsize:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig, ax = plt.subplots()

    # 4. Plotagem
    # style='driver_full_name' ajuda a diferenciar pilotos da mesma equipe (ex: linha tracejada vs sólida)
    # mas para ficar mais limpo, vamos usar apenas hue e markers.
    sns.lineplot(
        data=df_plot,
        x='race_name',
        y='points',
        hue='driver_full_name',
        palette=cores_pilotos, # O Seaborn vai tentar casar os nomes. Se não achar, usa cor default do ciclo.
        style='driver_full_name', # Adiciona estilos de linha diferentes para diferenciar (ex: Norris sólido, Piastri tracejado)
        markers=True,
        dashes=True, # Permite linhas tracejadas automáticas
        linewidth=3,
        markersize=8,
        ax=ax
    )

    # 5. Estilização
    ax.set_title(f"World Drivers Championship (WDC) Points - {ano}", fontsize=18, pad=20, fontweight='bold')
    ax.set_xlabel("Grand Prix", fontsize=12)
    ax.set_ylabel("Points", fontsize=12)
    
    # Grid apenas no eixo Y para facilitar leitura de pontuação
    ax.grid(axis='y', linestyle='--', alpha=0.6)
    
    # Rotacionar eixo X
    plt.xticks(rotation=45, ha='right')

    # Ajuste da Legenda
    ax.legend(title='Driver', bbox_to_anchor=(1.01, 1), loc='upper left', borderaxespad=0, frameon=False)

    # Anotação do Líder Final (Opcional, dá um charme data-driven)
    last_points = df_plot.groupby('driver_full_name').last()['points']
    for piloto, ponto in last_points.items():
        # Pega a ultima rodada desse piloto
        last_race_idx = df_plot[df_plot['driver_full_name'] == piloto]['race_name'].iloc[-1]
        # Plota o texto do lado direito
        # ax.text(x=len(df_plot['race_name'].unique())-1, y=ponto, s=f"{ponto:.0f}", va='center', fontsize=10, fontweight='bold')
        pass # Desativado por padrão para não poluir, ative se quiser os números na ponta da linha

    plt.tight_layout()

    # 6. Salvamento
    if save_fig:
        # Sanitiza nome
        nomes_str = "_".join([n.split()[-1] for n in pilotos_destaque]) # Pega só sobrenomes para o arquivo não ficar gigante
        filename_base = "".join(c for c in f'drivers_evolution_{ano}_{nomes_str}'.lower() if c.isalnum() or c in (' ', '_')).replace(' ', '_')
        filename = f"{filename_base}_safe.png"
        
        os.makedirs(save_path, exist_ok=True)
        full_path = os.path.join(save_path, filename)
        
        try:
            fig.savefig(full_path, bbox_inches='tight', dpi=300)
            print(f"Gráfico salvo em: {os.path.abspath(full_path)}")
        except Exception as e:
            print(f"Erro ao salvar o gráfico: {e}")

    plt.show()
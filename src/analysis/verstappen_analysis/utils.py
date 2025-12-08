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
    figsize: Optional[Tuple[int, int]] = (16, 9),
    save_fig: bool = False,
    save_path: str = 'grafs'
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
        if figsize:
            fig, ax = plt.subplots(figsize=figsize)
        else:
            fig, ax = plt.subplots()

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

        ax.axvline(media_base, color=cor_base, linestyle='--', label=f'Média {piloto_base.split(" ")[-1]}: {media_base:.2f}')
        ax.axvline(media_comparado, color=cor_comparado, linestyle='--', label=f'Média {piloto_comparado.split(" ")[-1]}: {media_comparado:.2f}')

        # Títulos e rótulos
        ax.set_title(f"Consistency Comparison: {piloto_base} vs. {piloto_comparado}")
        ax.set_xlabel("Driver Std. Dev. VS Avg. Std. Dev. (Lower = More Consistent) - ms")
        ax.set_ylabel("Frequency (nº of races)")

        # Atualiza a legenda para incluir a contagem de corridas
        handles, _ = ax.get_legend_handles_labels()
        labels = [f'{piloto_base} ({n_corridas_base} races)', f'{piloto_comparado} ({n_corridas_comparado} races)'] + [h.get_label() for h in handles[2:]]
        ax.legend(handles=handles, labels=labels)

        ax.grid(axis='y')

        if save_fig:
            # Sanitiza o título para um nome de arquivo válido
            filename_base = "".join(c for c in f'histograma_consistencia__{piloto_base}_vs_{piloto_comparado}'.lower() if c.isalnum() or c in (' ', '_')).replace(' ', '_')
            filename = f"{filename_base}_safe.png"
            
            # Garante que o diretório de destino exista
            os.makedirs(save_path, exist_ok=True)
            
            full_path = os.path.join(save_path, filename)
            try:
                fig.savefig(full_path, bbox_inches='tight')
                print(f"Gráfico salvo em: {os.path.abspath(full_path)}")
            except Exception as e:
                print(f"Erro ao salvar o gráfico: {e}")

        plt.show()

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
import seaborn as sns
import matplotlib.pyplot as plt

class Plotter:
    '''
    Classe criada para ajudar a gerar gráficos de forma mais fácil e rápida durante as análises exploratórias
    '''

    def barplot(
        self,
        df,
        x,
        y=None,
        filter_query=None,
        groupby=None,
        count_name="count",
        top_n=None,
        sort_by=None,
        ascending=False,
        palette="viridis",
        figsize=(12, 8),
        title=None,
        rotation=45,
        ha="right"
    ):
        """
        Gera um gráfico de barras usando Seaborn.

        Parâmetros:
        - df: DataFrame
        - x, y: colunas para eixo X e Y (se y for None, será usado groupby + contagem)
        - filter_query: string para filtrar com pandas.query()
        - groupby: coluna ou lista de colunas para agrupar (usado se y for None)
        - count_name: nome da coluna de contagem
        - top_n: pega apenas os N primeiros após ordenação
        - sort_by: coluna para ordenar (default = y ou count_name)
        - ascending: ordem da ordenação
        - palette: paleta do seaborn
        - figsize: tamanho da figura
        - title: título do gráfico
        - rotation: rotação dos rótulos do eixo X
        - ha: alinhamento horizontal dos rótulos do eixo X
        """
        data = df.copy()

        if filter_query:
            data = data.query(filter_query)

        if y is None:
            if not groupby:
                raise ValueError("Se 'y' não for informado, 'groupby' é obrigatório.")
            data = data.groupby(groupby).size().reset_index(name=count_name)
            y = count_name

        if sort_by is None:
            sort_by = y
        data = data.sort_values(sort_by, ascending=ascending)

        if top_n:
            data = data.head(top_n)

        fig, ax = plt.subplots(figsize=figsize)
        sns.barplot(data=data, x=x, y=y, palette=palette, ax=ax)

        ax.set_xticklabels(ax.get_xticklabels(), rotation=rotation, ha=ha)

        for container in ax.containers:
            ax.bar_label(container, fmt='%d', label_type='edge', padding=3)

        if title:
            ax.set_title(title)

        plt.tight_layout()
        plt.show()

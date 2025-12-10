from manim import *
from scipy.interpolate import make_interp_spline
import numpy as np
import os

class LineChampionshipChart(Scene):
    """
    Classe base modular para gráficos de campeonato de F1.
    """
    def __init__(
        self,
        df_grouped,             # DataFrame agrupado
        race_list,              # Lista de nomes das corridas
        team_colors,            # Dict de cores
        x_max,                  # Total de rodadas
        y_max,                  # Pontuação máxima Y
        axis_config=None,       # [NOVO] Configuração extra dos eixos (ticks, cores)
        logos_dir=None,         # Caminho logos
        logo_map=None,          # Mapa logos
        static_mode=False,      # Modo rápido
        show_gap=True,          # Mostrar gap
        transparent_bg=False,   # Fundo transparente
        font="Roboto Slab",     # Fonte
        color_highlight="#FFFFFF", # Cor destaque
        **kwargs
    ):
        self.df_grouped = df_grouped
        self.race_list = race_list
        self.team_colors = team_colors
        self.x_max = x_max
        self.y_max = y_max
        
        # [NOVO] Recebendo o dicionário de configuração dos eixos
        self.axis_config = axis_config if axis_config is not None else {}
        
        self.logos_dir = logos_dir
        self.logo_map = logo_map or {}
        
        self.static_mode = static_mode
        self.show_gap = show_gap
        self.transparent_bg = transparent_bg
        
        self.font = font
        self.color_axis = "#AAAAAA"
        self.color_highlight = color_highlight
        
        super().__init__(**kwargs)

    def construct(self):
        # Configuração de fundo (apenas se não for transparente)
        if not self.transparent_bg:
            self.camera.background_color = "#0a0a0a"

        # --- 1. CRIAÇÃO DOS ELEMENTOS ---
        ax, y_numbers, grid_group, x_lbl, y_lbl, x_label_mobs = self._create_axes()
        
        # Tracker principal de tempo
        race_progress = ValueTracker(self.x_max if self.static_mode else 0)
        
        # Objetos das Equipes
        logos_group, lines_group, team_splines, team_limits = self._create_team_objects(ax, race_progress)
        
        # Gap Dinâmico
        gap_dynamic = VGroup()
        if self.show_gap:
            # Usamos always_redraw para garantir que a linha tracejada não suma
            gap_dynamic = always_redraw(lambda: self._get_gap_visuals(ax, race_progress, team_splines, team_limits))
            gap_dynamic.set_z_index(10)

        # Título
        title = Text("World Constructors Championship", font=self.font, font_size=18, color=GRAY).to_edge(UP, buff=0.1)

        # --- 2. ANIMAÇÃO ---
        if self.static_mode:
            self.add(title, ax, y_numbers, grid_group, x_lbl, y_lbl, x_label_mobs)
            self.add(lines_group, logos_group, gap_dynamic)
            return

        # Sequência de Vídeo
        self.play(Write(title), run_time=1)
        self.play(Create(ax.x_axis), Create(ax.y_axis), run_time=2)
        
        self.play(
            FadeIn(grid_group),
            FadeIn(y_numbers),
            Write(x_lbl), Write(y_lbl),
            LaggedStart(*[FadeIn(l, shift=DOWN*0.2) for l in x_label_mobs], lag_ratio=0.05),
            run_time=2
        )

        self.play(Create(lines_group))
        
        if self.show_gap:
            self.add(gap_dynamic)
            
        self.play(LaggedStart(*[FadeIn(l, scale=0.5) for l in logos_group], lag_ratio=0.1), run_time=1.5)
        
        # A CORRIDA
        self.play(race_progress.animate.set_value(self.x_max), run_time=15, rate_func=linear)
        self.wait(3)

    # ================= MÉTODOS INTERNOS =================

    def _create_axes(self):
        # Cria os eixos usando o axis_config passado no init
        ax = Axes(
            x_range=[0, self.x_max, 1],
            y_range=[0, self.y_max, 50],
            x_length=12, y_length=6,
            axis_config=self.axis_config, # [USO DO NOVO PARAMETRO]
            x_axis_config={"font_size": 14, "label_direction": DOWN, 'include_numbers': False},
            y_axis_config={"font_size": 14, "label_direction": LEFT, 'include_numbers': True},
            tips=False
        ).shift(UP * 0.2)

        # Separa números Y para animar depois
        y_numbers = ax.y_axis.numbers
        ax.y_axis.remove(y_numbers)

        # Labels
        x_lbl = ax.get_x_axis_label(
            Text("Round", font=self.font, font_size=18, color=self.color_axis)
            .next_to(ax.x_axis, DOWN, buff=1).to_edge(RIGHT, buff=0.5)
        ).shift(DOWN * 0.2)
        
        y_lbl = ax.get_y_axis_label(
            Text("Points", font=self.font, font_size=18, color=self.color_axis)
            .next_to(ax.y_axis, UP, buff=0.2)
        )

        # Labels Rotacionados
        x_label_mobs = VGroup()
        for i, race_name in enumerate(self.race_list):
            t = Text(str(race_name), font_size=12, color=self.color_axis).scale(0.8)
            t.move_to(ORIGIN, aligned_edge=LEFT)
            t.rotate(-PI/4, about_point=ORIGIN)
            t.shift(ax.c2p(i, 0) + DOWN * 0.15 + LEFT * 0.1)
            x_label_mobs.add(t)

        # Grid
        grid_group = VGroup()
        for i in range(50, int(self.y_max), 50):
            grid_group.add(DashedLine(
                start=ax.c2p(0, i), end=ax.c2p(self.x_max, i),
                dash_length=0.1, color=self.color_axis, stroke_width=1, stroke_opacity=0.15
            ))
            
        return ax, y_numbers, grid_group, x_lbl, y_lbl, x_label_mobs

    def _create_team_objects(self, ax, tracker):
        logos_group = Group()
        lines_group = VGroup()
        team_splines = {}
        team_limits = {}

        for team, data in self.df_grouped:
            color = self.team_colors.get(team, WHITE)
            
            # Dados
            data_sorted = data.sort_values('round_id')
            try:
                x_raw = data_sorted['round_id'].values 
                if x_raw.min() > 1000: 
                    x_raw = x_raw - x_raw.min()
            except:
                x_raw = np.arange(len(data_sorted))

            y_raw = data_sorted['points'].values
            limit = x_raw.max()
            team_limits[team] = limit

            # Spline (Curva Suave)
            x_smooth = np.linspace(x_raw.min(), limit, 300)
            spline_func = make_interp_spline(x_raw, y_raw, k=3)
            team_splines[team] = spline_func
            y_smooth = np.maximum(spline_func(x_smooth), 0)

            # --- LOGO ---
            logo = self._get_logo(team, color)
            
            # [CRÍTICO] Updater robusto para sincronia
            # Usamos argumentos padrão (spl=spline_func) para "congelar" a função correta
            # para este time específico dentro do loop.
            def update_logo(mob, spl=spline_func, lim=limit):
                t = tracker.get_value()
                # Garante que o logo não ultrapasse o fim dos dados da equipe
                t_clamped = min(t, lim)
                # Pega a posição Y exata da spline naquele tempo
                y_pos = spl(t_clamped)
                # Move
                mob.move_to(ax.c2p(t_clamped, y_pos)).shift(RIGHT * 0.3)
            
            logo.add_updater(update_logo)
            logos_group.add(logo)

            # --- LINHA ---
            # Mesma técnica de congelamento de variáveis no lambda
            line = always_redraw(lambda x=x_smooth, y=y_smooth, c=color: 
                VGroup(
                    ax.plot_line_graph(x_values=x[x <= tracker.get_value()], y_values=y[x <= tracker.get_value()], line_color=c, add_vertex_dots=False, stroke_width=8, stroke_opacity=0.2),
                    ax.plot_line_graph(x_values=x[x <= tracker.get_value()], y_values=y[x <= tracker.get_value()], line_color=c, add_vertex_dots=False, stroke_width=3.5, stroke_opacity=1.0)
                )
            )
            lines_group.add(line)

        return logos_group, lines_group, team_splines, team_limits

    def _get_logo(self, team, color):
        if self.logos_dir and self.logo_map:
            filename = self.logo_map.get(team)
            full_path = os.path.join(self.logos_dir, filename) if filename else None
            if full_path and os.path.exists(full_path):
                return ImageMobject(full_path).set_width(0.28)
        return Dot(color=color, radius=0.08)

    def _get_gap_visuals(self, ax, tracker, splines, limits):
        t = tracker.get_value()
        if t < 1: return VGroup()

        scores = []
        for tm, spl in splines.items():
            try:
                limit = limits.get(tm, self.x_max)
                t_clamped = min(max(t, 0), limit)
                scores.append((float(spl(t_clamped)), tm, t_clamped))
            except: pass

        scores.sort(key=lambda x: x[0], reverse=True)
        if len(scores) < 2: return VGroup()

        p1_score, _, p1_t = scores[0]
        p2_score, _, p2_t = scores[1]
        
        # Sincronia: usa o menor tempo entre os dois para a linha vertical
        common_t = min(p1_t, p2_t)
        
        p1_pos = ax.c2p(common_t, p1_score)
        p2_pos = ax.c2p(common_t, p2_score)

        return VGroup(
            DashedLine(start=p2_pos, end=p1_pos, color=self.color_highlight, stroke_opacity=0.9, stroke_width=3),
            VGroup(
                Integer(number=int(p1_score - p2_score), color=self.color_highlight, font_size=24).set_gloss(0.5),
                Text("pts to 2nd", font=self.font, font_size=10, color=self.color_highlight)
            ).arrange(RIGHT, buff=0.1, aligned_edge=DOWN).next_to((p1_pos + p2_pos) / 2, RIGHT, buff=0.25)
        )
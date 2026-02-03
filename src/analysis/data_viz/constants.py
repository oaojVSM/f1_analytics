import matplotlib.colors as mcolors

TEAM_COLORS = {
    "Red Bull": "#3671C6",       # Azul Clássico
    "Mercedes": "#27F4D2",       # Verde/Ciano Petronas (brilha bem no escuro)
    "Ferrari": "#E80020",        # Rosso Corsa
    "McLaren": "#FF8000",        # Laranja Papaya
    "Aston Martin": "#229971",   # British Racing Green
    "Alpine": "#0090FF",         # Azul Alpine (Nota: às vezes usam rosa da BWT)
    "Williams": "#64C4FF",       # Azul Celeste
    "VCARB": "#6692FF",          # Azul 'Visa Cash App' (mais claro que a RBR)
    "Sauber": "#52E252",         # Verde Neon (Kick/Stake branding)
    "Haas": "#B6BABD",           # Cinza/Branco (neutro)
    "Cooper-Climax": '#004225'   # Verde Escuro (clássico)
}

JOLPICA_CONSTRUCTOR_RENAME = {
    'RB F1 Team': 'VCARB',
    'Haas F1 Team': 'Haas',
    'Alpine F1 Team': 'Alpine'
}

# Definição dos pilotos por equipe para geração dinâmica
DRIVERS_BY_TEAM = {
    "Red Bull": ["Verstappen", "Lawson", "Perez"],
    "Mercedes": ["Russell", "Antonelli"],
    "Ferrari": ["Leclerc", "Hamilton"],
    "McLaren": ["Norris", "Piastri"],
    "Aston Martin": ["Alonso", "Stroll"],
    "Alpine": ["Gasly", "Doohan", "Colapinto"],
    "Williams": ["Albon", "Sainz", "Sargeant"],
    "VCARB": ["Tsunoda", "Hadjar", "Ricciardo"],
    "Sauber": ["Hulkenberg", "Bortoleto", "Bottas", "Zhou"],
    "Haas": ["Ocon", "Bearman", "Magnussen"]
}

def _generate_driver_colors(drivers_map, team_colors):
    """
    Gera um dicionário flat de {piloto: cor} baseado nas equipes.
    Para o 1º piloto da lista, usa a cor base.
    Para o 2º piloto em diante, gera variações (mais claro ou mais escuro).
    """
    driver_colors = {}
    
    for team, drivers in drivers_map.items():
        base_hex = team_colors.get(team, "#333333") # Fallback dark grey
        
        try:
            base_rgb = mcolors.to_rgb(base_hex)
        except ValueError:
            base_rgb = (0.5, 0.5, 0.5)

        for i, driver in enumerate(drivers):
            if i == 0:
                # 1º Piloto: Cor Original da Equipe
                driver_colors[driver] = base_hex
            elif i == 1:
                # 2º Piloto: Tratamento Especial
                
                # Exceção Ferrari (Hamilton): Vermelho -> Mais Escuro (para não ficar rosa)
                if team == "Ferrari":
                    # Escurecer: Mistura com preto (0,0,0)
                    darker = [max(0, x * 0.7) for x in base_rgb]
                    driver_colors[driver] = mcolors.to_hex(darker)
                else:
                    # Padrão: Clarear (Mistura com branco)
                    # ratio 0.4 de branco
                    lighter = [x + (1 - x) * 0.4 for x in base_rgb]
                    driver_colors[driver] = mcolors.to_hex(lighter)
            else:
                # 3º+ Piloto (Reservas/Ex): Variações extras
                # Alterna entre ainda mais claro ou dessaturado
                factor = 0.6 + (i * 0.1) 
                tint = [min(1, x + (1 - x) * factor) for x in base_rgb]
                driver_colors[driver] = mcolors.to_hex(tint)
                
    return driver_colors

# Chamada automática para gerar o dicionário final
DRIVER_COLORS = _generate_driver_colors(DRIVERS_BY_TEAM, TEAM_COLORS)

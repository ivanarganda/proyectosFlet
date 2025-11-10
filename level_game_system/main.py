import math

def get_progress(score, low, high):
    """Devuelve el porcentaje completado del nivel actual (0 – 100 %)."""
    return round(((score - low) / (high - low)) * 100, 2)

def get_level_and_prestige(prestige: int, score: int, prestiges: dict):
    """
    Devuelve (nivel_actual, puntos_inicial_nivel, puntos_final_nivel, prestigio)
    Nivel 1 abarca de 0 hasta thresholds[0] (sin incluir el límite superior).
    Cuando score >= thresholds[i], pasa al siguiente nivel.
    """
    levels_prestige = prestiges.get(f"Prestige {prestige}", [])
    if not levels_prestige:
        print(f"⚠️ Prestigio {prestige} no encontrado.")
        return None, None, None, None

    # Si supera el último nivel
    if score >= levels_prestige[-1]:
        return len(levels_prestige), levels_prestige[-2], levels_prestige[-1], prestige

    # Nivel 1: 0 <= score < thresholds[0]
    if score < levels_prestige[0]:
        return 1, 0, levels_prestige[0], prestige

    # Recorremos niveles intermedios
    for i in range(1, len(levels_prestige)):
        prev_level_score = levels_prestige[i - 1]
        next_level_score = levels_prestige[i]

        # si el score está entre estos dos límites, pertenece al nivel (i+1)
        if prev_level_score <= score < next_level_score:
            current_level = i + 1
            return current_level, prev_level_score, next_level_score, prestige

    # Por seguridad
    return len(levels_prestige), levels_prestige[-2], levels_prestige[-1], prestige


# ========================================
# CONFIGURACIÓN
# ========================================
levels = 100                # niveles por prestigio
prestiges_total = 10        # cantidad total de prestigios
base_rate = 1.12            # crecimiento de dificultad (suave)
base_score = 100            # puntos base para el nivel 1
soften_every = 25           # cada cuántos niveles se suaviza la progresión
soften_amount = 0.03        # reducción del rate cada bloque
prestige_difficulty_rate = 0.0015  # +0.15% de dificultad por prestigio

# ========================================
# GENERACIÓN DE PRESTIGIOS
# ========================================
prestiges = {}

for k in range(prestiges_total):
    thresholds = []
    current_target_score = base_score
    rate_level = base_rate + (k * prestige_difficulty_rate)

    for i in range(levels):
        thresholds.append(round(current_target_score, 0))

        # suaviza un poco la curva cada X niveles
        if (i + 1) % soften_every == 0 and rate_level > 1.02:
            rate_level -= soften_amount

        current_target_score *= rate_level

    thresholds = list(map(lambda x: math.floor(x), thresholds)) 
    prestiges[f"Prestige {k + 1}"] = thresholds

# ========================================
# RESULTADOS
# ========================================
player_score = 101
prestige = 1

level, points_current_level, points_left_next_level, prestige = get_level_and_prestige(prestige,player_score, prestiges)

progress = get_progress(player_score, points_current_level, points_left_next_level)

global_score = player_score
if prestige > 1:
    for p in range(1, prestige):
        global_score += prestiges[f"Prestige {p}"][-1]

print( f"""
Prestige {prestige} 
Level {level}:
From {points_current_level} to {points_left_next_level}
Total score: {global_score}
Current score: {player_score}
Progress {progress}%
""" )

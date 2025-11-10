import math
import json
import os

def get_player_status(prestige: int, score: int, file: str):
    """
    Devuelve:
    (level, prestige, low, high, score_local, progress_level, progress_global, global_score, title)
    con auto-prestige automático si supera el total del prestigio actual.
    """

    # ===============================
    # FUNCIONES INTERNAS
    # ===============================
    def get_total_global_score(prestiges: dict) -> int:
        """Suma el último nivel de cada prestigio (puntuación máxima global)."""
        return sum(levels[-1] for levels in prestiges.values() if levels)

    def get_progress(score, low, high):
        """Porcentaje dentro del nivel actual (0–100%)."""
        if high <= low:
            return 100.0
        return round(((score - low) / (high - low)) * 100, 2)

    def get_level_and_prestige(prestige: int, score: int, prestiges: dict):
        """
        Devuelve (nivel_actual, low, high, prestigio_actual, score_local)
        con reinicio automático si supera el prestigio actual.
        """
        while True:
            key = f"Prestige {prestige}"
            levels = prestiges.get(key, [])
            if not levels:
                raise ValueError(f"Prestige {prestige} no encontrado en {file}")

            max_score = levels[-1]

            # ✅ Si se pasa del prestigio actual, avanza al siguiente y reinicia score
            if score >= max_score:
                score -= max_score
                prestige += 1
                # Si no existe el siguiente prestigio, se queda en el último
                if f"Prestige {prestige}" not in prestiges:
                    prestige -= 1
                    score = max_score
                    break
                continue

            # Determinar nivel dentro del prestigio actual
            if score < levels[0]:
                return 1, 0, levels[0], prestige, score

            for i in range(1, len(levels)):
                prev_score = levels[i - 1]
                next_score = levels[i]
                if prev_score <= score < next_score:
                    return i + 1, prev_score, next_score, prestige, score

            # Si no entra en el bucle (nivel máximo)
            return len(levels), levels[-2], levels[-1], prestige, score

    # ===============================
    # LECTURA DEL ARCHIVO JSON
    # ===============================
    BASE_DIR = os.path.dirname(__file__)
    JSON_PATH = os.path.join(BASE_DIR, file)

    if not os.path.exists(JSON_PATH):
        raise FileNotFoundError(f"No se encontró el archivo: {JSON_PATH}")

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        prestiges = json.load(f)

    # ===============================
    # CÁLCULOS PRINCIPALES
    # ===============================
    level, low, high, prestige, score_local = get_level_and_prestige(prestige, score, prestiges)
    progress_level = get_progress(score_local, low, high)

    # Calcular puntuación global total
    global_score = score_local + sum(
        prestiges[f"Prestige {p}"][-1] for p in range(1, prestige) if f"Prestige {p}" in prestiges
    )

    total_possible = get_total_global_score(prestiges)
    progress_global = round((global_score / total_possible) * 100, 2)

    title = file.split("_")[0]

    # ===============================
    # DEVOLVER RESULTADO
    # ===============================
    return level, prestige, low, high, score_local, progress_level, progress_global, global_score, title


# ========================================
# EJEMPLO DE USO
# ========================================
if __name__ == "__main__":
    level, prestige, low, high, score_local, progress_level, progress_global, global_score, title = get_player_status(
        1, 900, "tetris_levels.json"
    )

    print(f"""
    ==========================
    {title.upper()} PLAYER PROGRESSION
    ==========================
    Prestige {prestige}
    Level {level}
    From {low} to {high}
    Score (local): {score_local}
    Progress (level): {progress_level} %
    Global progress: {progress_global} %
    --------------------------
    Global Score: {global_score}
    ==========================
    """)

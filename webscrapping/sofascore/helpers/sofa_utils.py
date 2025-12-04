import re
# ==========================================
# UTILS
# ==========================================
def safe_get(obj, key, default=None):

    """Devuelve obj[key] si existe y obj es dict."""
    return obj.get(key, default) if isinstance(obj, dict) else default


def extraer_año_temporada(nombre):

    """Extrae año de cadena tipo '2024/25'."""
    if isinstance(nombre, int):
        return 2000 + nombre

    nombre = str(nombre)

    # 4 cifras → 2023
    if m := re.search(r"(20\d{2})", nombre):
        return int(m.group(1))

    # 2 cifras en XX/XX
    if m := re.search(r"(\d{2})/\d{2}", nombre):
        return 2000 + int(m.group(1))

    # Últimas dos
    if m := re.search(r"(\d{2})$", nombre):
        return 2000 + int(m.group(1))

    return None
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "DatabaseORM"))

import re
import requests
import pandas as pd
from datetime import datetime
from DatabaseORM.SQLiteORM import *
from params import HEADERS

# ==========================================
# CONFIGURACIÓN DE LA BD
# ==========================================
db = SQLiteORM("futbol.db")
db.connect_DB()

# Lista global donde guardaremos resultados
partidos = []

# Base del proxy
PROXY = "http://localhost:3000"


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


# ==========================================
# PETICIONES AL PROXY (ADAPTADAS A LALIGA)
# ==========================================
def obtener_temporadas_laliga():
    """Obtiene todas las temporadas de LaLiga desde el proxy."""
    url = f"{PROXY}/laliga/temporadas"
    data = requests.get(url).json()

    resultado = []
    for t in data.get("seasons", []):
        year_end = int(t["year"].split("/")[-1])
        name = t["name"]

        # Filtrar temporadas antiguas o que no correspondan a LaLiga
        if year_end < 21:
            continue

        resultado.append({
            "id": t["id"],
            "nombre": name
        })

    return resultado


def obtener_jornadas(id_temporada):
    """Devuelve la jornada actual y lista de rondas."""
    url = f"{PROXY}/laliga/temporada/{id_temporada}/jornadas"
    data = requests.get(url).json()
    return data["currentRound"], data["rounds"]


def obtener_partidos_ronda(id_temporada, ronda):
    """Obtiene los partidos de una ronda usando el proxy."""
    url = f"{PROXY}/laliga/temporada/{id_temporada}/jornada/{ronda}"
    resp = requests.get(url).json()

    # En nuestro proxy, esto SIEMPRE es una lista limpia
    if isinstance(resp, list):
        return resp

    return resp.get("events", [])


# ==========================================
# PROCESAMIENTO DE TEMPORADA
# ==========================================
def procesar_temporada(id_temporada, nombre_temporada):
    """Obtiene 1 partido por ronda exceptuando la ronda actual."""

    global partidos

    año_inicio = extraer_año_temporada(nombre_temporada)
    año_actual = datetime.now().year

    if año_inicio is None:
        print("⚠ No se pudo extraer año:", nombre_temporada)
        return False

    # Solo temporada actual y anterior
    if año_inicio not in (año_actual, año_actual - 1):
        print("⏭ Temporada antigua:", nombre_temporada)
        return False

    current_round, rounds = obtener_jornadas(id_temporada)

    for r in rounds:
        ronda = safe_get(r, "round")

        if ronda == current_round:
            continue

        eventos = obtener_partidos_ronda(id_temporada, ronda)

        if not eventos:
            continue

        # Guardar solo el primer partido de cada ronda
        partidos.append(eventos[0])

    return True


# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":

    temporadas = obtener_temporadas_laliga()

    for temporada in temporadas:
        id_temp = temporada["id"]
        nombre = temporada["nombre"]

        print(f"\nProcesando temporada: {nombre}")

        procesar_temporada(id_temp, nombre)

        print("Partidos recopilados:", len(partidos))

        df = pd.DataFrame(partidos)
        print(df)

        break  # quítalo para procesar TODAS las temporadas
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


# ==========================================
# UTILS
# ==========================================
def safe_get(obj, key, default=None):
    """Devuelve obj[key] si existe y obj es dict, si no devuelve default."""
    return obj.get(key, default) if isinstance(obj, dict) else default


def extraer_año_temporada(nombre):
    """Extrae un año a partir de expresiones tipo '2024/25' o 'LaLiga 25'."""
    if isinstance(nombre, int):
        return 2000 + nombre

    nombre = str(nombre)

    # 4 cifras → 2023
    if m := re.search(r"(20\d{2})", nombre):
        return int(m.group(1))

    # 2 cifras en formato XX/XX
    if m := re.search(r"(\d{2})/\d{2}", nombre):
        return 2000 + int(m.group(1))

    # Últimas 2 cifras sueltas
    if m := re.search(r"(\d{2})$", nombre):
        return 2000 + int(m.group(1))

    return None


# ==========================================
# PETICIONES AL PROXY
# ==========================================
def obtener_temporadas_laliga():
    """Obtiene todas las temporadas de LaLiga desde el proxy."""
    url = "http://localhost:3000/temporadas"
    data = requests.get(url).json()

    resultado = []
    for t in data.get("seasons", []):
        year_end = int(t["year"].split("/")[-1])
        name = t["name"]

        if year_end < 21: 
            continue
        if "Primera Division" in name:
            continue

        resultado.append({
            "id": t["id"],
            "nombre": name
        })

    return resultado


def obtener_jornadas(id_liga):
    """Devuelve la jornada actual y el listado de todas las rondas."""
    url = f"http://localhost:3000/jornadas/{id_liga}"
    data = requests.get(url).json()
    return data["currentRound"], data["rounds"]


def obtener_partidos_ronda(id_liga, ronda):
    """Obtiene los eventos de una ronda (devueltos por tu API de Node)."""
    url = f"http://localhost:3000/partidos/{id_liga}/{ronda}"
    resp = requests.get(url).json()

    if isinstance(resp, list):
        return resp   # ya viene mapeado desde Node.js (si usas la versión avanzada)

    # si viene en formato viejo:
    return resp.get("events", [])


# ==========================================
# PROCESAMIENTO DE TEMPORADA
# ==========================================
def procesar_temporada(id_liga, nombre_temporada):
    """Obtiene 1 partido por ronda (excepto ronda actual)."""

    global partidos

    año_inicio = extraer_año_temporada(nombre_temporada)
    año_actual = datetime.now().year

    if año_inicio is None:
        print("⚠ No se pudo extraer año:", nombre_temporada)
        return False

    # Solo temporadas actual o pasada
    if año_inicio not in (año_actual, año_actual - 1):
        print("⏭ Temporada antigua:", nombre_temporada)
        return False

    current_round, rounds = obtener_jornadas(id_liga)

    for r in rounds:
        ronda = safe_get(r, "round")

        if ronda == current_round:
            continue

        eventos = obtener_partidos_ronda(id_liga, ronda)

        if not eventos:
            continue

        # Guardar solo el primer evento de esta ronda
        partidos.append(eventos[0])
        
    return True

# ==========================================
# MAIN: PROCESAR TODAS LAS TEMPORADAS
# ==========================================
if __name__ == "__main__":

    for temporada in obtener_temporadas_laliga():

        id_liga = temporada["id"]
        nombre = temporada["nombre"]

        print(f"Procesando temporada: {nombre}")

        procesar_temporada(id_liga, nombre)

        print("Partidos recopilados:", len(partidos))

        df = pd.DataFrame(partidos)
        print(df)

        break  # eliminar si quieres procesar TODAS las temporadas

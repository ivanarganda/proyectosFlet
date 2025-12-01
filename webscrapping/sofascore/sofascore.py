import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "DatabaseORM"))
from DatabaseORM.SQLiteORM import *
import re
import requests
from datetime import datetime
import json
import pandas as pd

db = SQLiteORM("futbol.db")

db.connect_DB()

HEADERS = {
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8,"
        "application/signed-exchange;v=b3;q=0.7"
    ),
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "es-ES,es;q=0.9,en-GB;q=0.8,en;q=0.7,en-US;q=0.6,zh-CN;q=0.5,zh;q=0.4",
    "Cache-Control": "max-age=0",
    "If-None-Match": "\"1b3ddd626a\"",
    "Priority": "u=0, i",
    "Sec-Ch-Ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/142.0.0.0 Safari/537.36"
    )
}

from datetime import datetime
import re
from datetime import datetime

def extraer_año_temporada(nombre):
    if isinstance(nombre, int):
        return 2000 + nombre  # ej: 25 → 2025

    nombre = str(nombre)

    match_4 = re.search(r"(20\d{2})", nombre)
    if match_4:
        return int(match_4.group(1))

    match_2 = re.search(r"(\d{2})/\d{2}", nombre)
    if match_2:
        return 2000 + int(match_2.group(1))

    match_suelto = re.search(r"(\d{2})$", nombre)
    if match_suelto:
        return 2000 + int(match_suelto.group(1))

    return None

def obtener_partidos_ronda(id_liga, ronda):

    print( id_liga, ronda )

    url = f"http://localhost:3000/partidos/{id_liga}/{ronda}"

    resp = requests.get(url).json()

    print( resp )

    if resp is None:
        return []

    return resp.get("events", [])

def procesar_temporada(id_liga, nombre_temporada):

    año_inicio = extraer_año_temporada(nombre_temporada)
    año_actual = datetime.now().year

    # Validación temporada
    if año_inicio is None:
        print("No se puede extraer año:", nombre_temporada)
        return []

    if año_inicio not in (año_actual, año_actual - 1):
        print("Temporada antigua:", nombre_temporada)
        return []

    # Obtener jornadas
    current_round, rounds = obtener_jornadas(id_liga)

    partidos_totales = []

    for r in rounds:

        ronda = r.get("round")

        # Evitar ronda actual
        if ronda == current_round:
            continue

        eventos = obtener_partidos_ronda(id_liga, ronda)

        if not eventos:
            continue

        partidos_totales.extend(eventos)

        break

    return partidos_totales


def obtener_jornadas( id_liga ):

    url = f"http://localhost:3000/jornadas/{id_liga}"
    data = requests.get(url).json()

    return data["currentRound"] , data["rounds"]



# ===========================================
# Obtener temporada actual
# ===========================================
def obtener_temporadas_laliga():

    url = "http://localhost:3000/temporadas"
    data = requests.get(url).json()

    temporadas = data.get("seasons", [])

    resultado = []
    for t in temporadas:
        if int(t["year"].split("/")[-1]) < 21 or "Primera Division" in t["name"]: continue
        resultado.append({
            "id": t["id"],
            "nombre": t["name"]
        })

    return resultado


# Probarlo
partidos = None

for temporada in obtener_temporadas_laliga():

    id_liga = temporada["id"]
    nombre = temporada["nombre"]

    print("Procesando temporada:", nombre)

    partidos = procesar_temporada(id_liga, nombre)

    df = pd.DataFrame(partidos)

    break

print( partidos )
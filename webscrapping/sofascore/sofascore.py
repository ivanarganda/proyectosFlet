import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "DatabaseORM"))
import re
import requests
import pandas as pd
from datetime import datetime
from DatabaseORM.SQLiteORM import *
from params import HEADERS
from helpers.sofa_utils import *
import json
import requests
from requests.exceptions import ConnectionError, Timeout, RequestException

def safe_request(url, timeout=40):
    """
    Realiza una petición segura al proxy y maneja TODOS los errores comunes.
    Retorna:
        - dict JSON válido
        - {} si falla
    """
    try:
        resp = requests.get(url, timeout=timeout)

        # Si responde pero con código != 200
        if resp.status_code != 200:
            print(f"❌ Error HTTP {resp.status_code} en {url}")
            return {}

        # Intentar parsear JSON
        try:
            return resp.json()
        except json.JSONDecodeError:
            print(f"❌ No se pudo decodificar JSON en: {url}")
            print("Respuesta cruda:", resp.text[:200])
            return {}

    except ConnectionError as ce:
        print(f"❌ No se pudo conectar con el proxy: {url}")
        print(f"Motivo: {ce}")
        print("¿El proxy Node.js está encendido?")
        return {}

    except Timeout:
        print(f"❌ Timeout esperando respuesta de: {url}")
        return {}

    except RequestException as e:
        print(f"❌ Error inesperado al hacer request a: {url}")
        print(e)
        return {}

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
# PETICIONES AL PROXY (ADAPTADAS A LALIGA)
# ==========================================
def obtener_temporadas_laliga():

    """Obtiene todas las temporadas de LaLiga desde el proxy."""
    url = f"{PROXY}/laliga/temporadas"
    data = safe_request(url)

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

def transformar_equipos(data):

    equipos_raw = data.get("teams", [])
    equipos = []
    ids = []

    for t in equipos_raw:

        equipos.append((
            t["id"],
            t["name"],
            t["slug"],
            ""
        ))

        ids.append(t["id"])

    return ids,equipos

def obtener_equipos(id_temporada):

    url = f"{PROXY}/laliga/equipos/{id_temporada}"
    data = safe_request(url)
    return data

def obtener_estadios(id_equipo):

    url = f"{PROXY}/laliga/estadios/{id_equipo}"
    data = safe_request(url)

    estadios_raw = data
    estadios = []

    for e in estadios_raw:

        estadios.append(
            (
                estadios_raw.get("id_estadio"),
                estadios_raw.get("nombre","Unknown"),
                estadios_raw.get("ciudad",{}).get("name","Unknown"),
                estadios_raw.get("capacidad",0),
                id_equipo
            )
        )

    return estadios

def obtener_jugadores(id_equipo):

    url = f"{PROXY}/laliga/equipo/{id_equipo}/jugadores"
    data = safe_request(url)

    jugadores_raw = data.get("players",[])
    jugadores = []

    for j in jugadores_raw:

        p = j.get("player",{})

        jugadores.append((
            p.get("id"),
            p.get("name","Unknown"),
            p.get("dateOfBirth","No date"), # convertir a edad
            p.get("team", "Unknown").get("gender","No identified"),
            id_equipo
        ))

    return jugadores


def obtener_jornadas(id_temporada):

    """Devuelve la jornada actual y lista de rondas."""
    url = f"{PROXY}/laliga/temporada/{id_temporada}/jornadas"
    data = safe_request(url)
    return data["currentRound"], data["rounds"]


def obtener_partidos_ronda(id_temporada, ronda):

    """Obtiene los partidos de una ronda usando el proxy."""
    url = f"{PROXY}/laliga/temporada/{id_temporada}/jornada/{ronda}"
    resp = safe_request(url)

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

    # Procesar los del primero grupo 1
    # equipos, usuarios, temporadas

    """ Temporadas """
    temporadas = obtener_temporadas_laliga()
    temporadas = list(filter(lambda x: "Division" not in x["nombre"], temporadas))

    nuevas_temporadas = []
    ids_temporadas = []

    equipos = []
    ids_equipos = []

    estadios = []

    for temp in temporadas:
        year_start, year_end = temp["nombre"].split(" ")[-1].split("/")

        nuevas_temporadas.append((
            temp["id"],
            temp["nombre"],
            int(year_start),
            int(year_end),
            8,
            db.datetime()
        ))
        
        ids_temporadas.append( temp["id"] )

    db.insert_many(
        table_name="temporadas",
        items=nuevas_temporadas
    )

    """ equipos """
    for id_temporada in ids_temporadas:

        data = obtener_equipos(id_temporada)
        ids, equipos = transformar_equipos( data )
        if ids not in ids_equipos:
            ids_equipos.append(ids)
        print( f"Equipos de temporada {id_temporada}: {len(equipos)}" )

    db.insert_many(
        table_name="equipos",
        items=equipos
    )   

    # Procesar los del grupo 2
    # estadios, jornadas, jugadores
    """ Jugadores y estadios ya que comparten el id_quipo """
    ids_equipos_planned = sorted(set(x for sub in ids_equipos for x in sub))
    
    for id_equipo in ids_equipos_planned:

        estadios.append(obtener_estadios( id_equipo ))
        
        jugadores = obtener_jugadores( id_equipo )

        print( f"Insertando jugadores del equipo {id_equipo}" )

        db.insert_many(
            table_name="jugadores",
            items=jugadores
        )

    estadios = [sublista[0] for sublista in estadios]

    db.insert_many(
        table_name="estadios",
        items=estadios
    )

    # Procesar los del grupo 3
    # partidos
    # for temporada in temporadas:
    #     id_temp = temporada["id"]
    #     nombre = temporada["nombre"]

    #     print(f"\nProcesando temporada: {nombre}")

    #     procesar_temporada(id_temp, nombre)

    #     print("Partidos recopilados:", len(partidos))

    #     df = pd.DataFrame(partidos)
    #     print(df)

    #     break  # quítalo para procesar TODAS las temporadas

    # Procesar los del grupo 4
    # stats_equipo_partido

    # Procesar los del grupo 5
    # stats_jugador_partido

    # Procesar los del grupo 6
    # reportes

    # Procesar los del grupo 7
    # reportes_partidos, reportes_jugadores
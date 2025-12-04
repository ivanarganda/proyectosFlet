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

def tabla_vacia(db, tabla: str) -> bool:
    sql = f"SELECT COUNT(*) AS total FROM {tabla}"
    result = db.execute_query(sql).json[0]["total"]
    print(result)
    return result == 0

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
jornadas = []

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


def transformar_partidos(id_temporada):
    # """
    # Obtiene TODOS los partidos de una temporada.
    
    # 1️⃣ Si existe /events → usa modo rápido
    # 2️⃣ Si no, recorre rondas
    # 3️⃣ Devuelve una lista unificada y normalizada
    # """

    # print(f"🔍 Consultando temporada {id_temporada}...")

    # partidos = []

    # for ev in eventos:
    #     partidos.append({
    #         "id_partido": ev.get("id"),
    #         "inicio": ev.get("startTimestamp"),
    #         "estado": ev.get("status", {}).get("type"),
    #         "id_local": ev.get("homeTeam", {}).get("id"),
    #         "id_visitante": ev.get("awayTeam", {}).get("id"),
    #         "goles_local": ev.get("homeScore", {}).get("current", 0),
    #         "goles_visitante": ev.get("awayScore", {}).get("current", 0),
    #         "id_estadio": ev.get("venue", {}).get("id"),
    #         "nombre_estadio": ev.get("venue", {}).get("stadiumName"),
    #     })

    # print(f"✅ Total partidos recopilados: {len(partidos)}")

    return []

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
    return data


def obtener_partidos_ronda(id_temporada, ronda):

    """Obtiene los partidos de una ronda usando el proxy."""
    url = f"{PROXY}/laliga/temporada/{id_temporada}/jornada/{ronda}"
    resp = safe_request(url)

    # En nuestro proxy, esto SIEMPRE es una lista limpia
    if isinstance(resp, list):
        return resp

    return resp.get("events", [])


# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":

    # Procesar los del primero grupo 1
    # equipos, usuarios, temporadas

    ids_temporadas = []
    ids_equipos = []
    scrapped_tables = []
    todos_los_partidos = []

    """ Temporadas """
    if tabla_vacia(db, "temporadas") or tabla_vacia(db, "equipos"):

        temporadas = obtener_temporadas_laliga()
        temporadas = list(filter(lambda x: "Division" not in x["nombre"], temporadas))

        nuevas_temporadas = []
        equipos = []
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

        ids_equipos = sorted(set(x for sub in ids_equipos for x in sub))

    else:

        ids_temporadas = list(
            i.get("id_temporada") for i in db.execute_query("SELECT DISTINCT id_temporada FROM temporadas").json
        )

        ids_equipos = list(
            i.get("id_equipo") for i in db.execute_query("SELECT DISTINCT id_equipo FROM equipos").json
        )

        scrapped_tables_ = [ "temporadas", "equipos" ]
        scrapped_tables = scrapped_tables_[:]

        # # Procesar los del grupo 2
        # # estadios, jornadas, jugadores

    ids_jornadas = []
    if tabla_vacia(db, "jornadas") or tabla_vacia( db, "jugadores") or tabla_vacia( db, "estadios"):

        """ jornadas """
        jornadas = []
        for id_temporada in ids_temporadas:
            for r in obtener_jornadas(id_temporada)["rounds"]:
                jornadas.append(( r["round"] , id_temporada, db.datetime() )) 
                ids_jornadas.append( r["round"] )

        db.insert_many(
            table_name="jornadas",
            items=jornadas
        )

        """ Jugadores y estadios ya que comparten el id_quipo """
        
        ids_jornadas = sorted(set(x for sub in ids_jornadas for x in sub))
        
        for id_equipo in ids_equipos:

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

    else:

        ids_jornadas = list(
            i.get("id_jornada") for i in db.execute_query("SELECT DISTINCT id_jornada FROM jornadas").json
        )

        scrapped_tables_ = scrapped_tables + [ "jornadas", "estadios" , "jugadores" ] if len(scrapped_tables) > 0 else [ "jornadas", "estadios" , "jugadores" ]
        scrapped_tables = scrapped_tables_[:]

    # En este caso no hace falta recuperar los ids de equipo, estadio o jornada ya que la propio endpoint y las jornadas y temporadas se coge ya de los ids recuperados anteriormente
    if len(scrapped_tables) > 0:
        print( f"Tables { ",".join(scrapped_tables) } are already scrapped" )

    print( ids_temporadas , ids_equipos , ids_jornadas )
    nombre_temporadas = list(
        i.get("nombre") for i in db.execute_query("SELECT DISTINCT nombre FROM temporadas").json
    )

    anios_temporada = list( extraer_año_temporada(i) for i in nombre_temporadas )
    # # Procesar los del grupo 3
    # # partidos ( ya podemos sacar consultas porque hay suficientes datos para sacarlo desde consultas sql )
    id_estadios = list ( i.get("id_estadio") for i in db.execute_query(
        "SELECT DISTINCT id_estadio FROM estadios"
    ).json)

    id_equipos = list( i.get("id_equipo") for i in db.execute_query(
        "SELECT DISTINCT id_equipo FROM estadios"
    ).json)

    print( id_estadios, id_equipos, ids_jornadas )

    for id_temporada in ids_temporadas:
        for ronda in ids_jornadas:
            partido = obtener_partidos_ronda(id_temporada, ronda)
            for p in partido:
                todos_los_partidos.append(
                    (
                        p.get("id"),
                        id_temporada,
                        ronda,
                        p.get("id_local"),
                        p.get("id_visitante"),
                        id_estadios[ id_equipos.index( p.get("id_local") )],
                        p.get("inicio"),
                        p.get("estado_partido"),
                        p.get("goles_local"),
                        p.get("goles_visitante")
                    )
                )
                print(f"Partido {p.get("id")} de la jornada {ronda}")
            print(f"Preparando {ronda}º jornada de la temporada {nombre_temporadas[ids_temporadas.index(id_temporada)]}")   
      
    db.insert_many( 
        table_name="partidos",
        items=todos_los_partidos 
    )
    
    # Procesar los del grupo 4
    # stats_equipo_partido

    # Procesar los del grupo 5
    # stats_jugador_partido

    # Procesar los del grupo 6
    # reportes

    # Procesar los del grupo 7
    # reportes_partidos, reportes_jugadores
import os
import logging
import re
from fastapi import FastAPI, Request, Depends, HTTPException, BackgroundTasks, Response
from dotenv import load_dotenv
from ivbox.SQLiteORM import *
from init_data import init_tables
from init_files import run_init_files
from prediccion_siguiente_jornada import predict
from params import DB,INITTED_FOLDER,SCRAPPING_FOLDER
from scrapping_state import SCRAPING_STATUS
from scrap import run_scrapping
import pandas as pd
import glob
from pathlib import Path 
import time
import datetime
import random
import requests
from typing import Optional
from helpers.sofa_utils import read_file, color_from_name
from collections import defaultdict
# --------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------

logging.basicConfig(
    filename="process.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv()

app = FastAPI(
    title="SofaScore Backend",
    version="1.0.0",
    description="Backend API for SofaScore Scraping + DB"
)

db: SQLiteORM | None = None

def get_db():
    db = SQLiteORM(DB)
    db.connect_DB()
    try:
        yield db
    finally:
        db.close_connection()

def date_field( date_field ):
    return f"""datetime(
            substr({date_field}, 7, 4) || '-' || 
            substr({date_field}, 4, 2) || '-' || 
            substr({date_field}, 1, 2) || ' ' || 
            substr({date_field}, 12)
        )"""

# QUERY
def BuildQuery(db: SQLiteORM, sql: str, filters: dict = {}):

    if filters:

        where_clauses = []
        params = []

        # Procesar filtros
        for key, value in filters.items():

            if value in (None, "", "None"):
                continue

            try:
                value = int(value)
            except:
                pass

            where_clauses.append(f"{key} = ?")
            params.append(value)

        # Si no hay filtros, ejecutamos tal cual
        if not where_clauses:
            return db.execute_query(sql).json

        # Unir filtros con AND
        and_conditions = " AND " + " AND ".join(where_clauses)

        # Insertar justo después del WHERE 1=1
        sql = re.sub(
            r"(WHERE\s*1\s*=\s*1)",
            r"\1" + and_conditions,
            sql,
            flags=re.IGNORECASE
        )

        params = tuple(params)

        print("SQL FINAL:", sql)
        print("PARAMS:", params)

        return db.execute_query(sql, params).json
    
    return db.execute_query(sql).json

# --------------------------------------------------------------------
# STARTUP EVENT  (equivalente a handle_server)
# --------------------------------------------------------------------

@app.on_event("startup")
def startup_event():

    try:

        logging.info("✅ Server started and DB initialized")

    except Exception as e:
        logging.error(str(e))
        raise


# --------------------------------------------------------------------
# HELPERS
# --------------------------------------------------------------------

def parse_json_response(message, status: int = 200):
    return {
        "message": message,
        "status": status
    }

def init_progress_cb(step, current, total):
    global_progress_adapter(
        module="Init",
        step=step,
        current=current,
        total=total,
        weight=40,   # Ocupa de 0% a 40%
        offset=0
    )

def scrap_progress_cb(step, current, total):
    global_progress_adapter(
        module="Scraping",
        step=step,
        current=current,
        total=total,
        weight=60,   # Ocupa del 40% al 100%
        offset=40
    )



def scrapping_progress_cb(step, current, total):
    # scraping ocupa 60% del progreso total
    global_progress_adapter(
        module="Scraping",
        step=step,
        current=current,
        total=total,
        weight=60,     # 40% a 100%
        offset=40
    )


def global_progress_adapter(module, step, current, total, weight, offset):
    if total is None or total == 0:
        local_ratio = 0
    else:
        local_ratio = current / total  

    module_progress = local_ratio * weight
    global_progress = offset + module_progress

    if global_progress > 100:
        global_progress = 100

    # 👉 Forzamos variación mínima para que Flet refresque
    SCRAPING_STATUS["current"] = round(global_progress, 2) + random.random() * 0.0001
    SCRAPING_STATUS["total"] = 100

    SCRAPING_STATUS["step"] = f"{module}: {step}"

def full_scraping_task():

    try:
        SCRAPING_STATUS.update({
            "running": True,
            "finished": False,
            "current": 0,
            "total": 100,
            "step": "Inicializando...",
            "error": None
        })

        # 1) INIT FILES 0% → 40%
        run_init_files(init_progress_cb)

        # 2) SCRAP 40% → 100%
        run_scrapping(scrap_progress_cb)

        SCRAPING_STATUS["running"] = False
        SCRAPING_STATUS["finished"] = True

        global_progress_adapter(
            step="Completado",
            current=1,
            total=1,
            module="Finish",
            weight=1,
            offset=99
        )

    except Exception as e:
        SCRAPING_STATUS["error"] = str(e)
        SCRAPING_STATUS["running"] = False

def progress_callback(step, current=None, total=None):

    SCRAPING_STATUS["running"] = True
    SCRAPING_STATUS["step"] = step

    if current is not None:
        SCRAPING_STATUS["current"] = current
    if total is not None:
        SCRAPING_STATUS["total"] = total

    # ✅ FIN
    if current is not None and total is not None and current >= total:
        SCRAPING_STATUS["running"] = False
        SCRAPING_STATUS["finished"] = True


# --------------------------------------------------------------------
# AUTHORIZATION DEPENDENCY
# --------------------------------------------------------------------

def check_authorization(request: Request, db: SQLiteORM = Depends(get_db)):
    auth_header = request.headers.get("Authorization")

    if not auth_header or "Bearer " not in auth_header:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        token = auth_header.split(" ")[1]
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid token format")

    result = db.execute_query(
        "SELECT * FROM usuarios WHERE token = ?",
        (token,)
    ).json

    if not result:
        raise HTTPException(status_code=401, detail="Invalid token")

    return True


# --------------------------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/init_data")
def init_data():
    if init_tables() is False:
        raise RuntimeError("❌ Unable initializing database tables")
    return parse_json_response("Scrapped ✅",200)

# --------------------------------------------------------------------
# PROTECTED TEST ENDPOINT
# --------------------------------------------------------------------

@app.get("/protected")
def protected_route(auth: bool = Depends(check_authorization)):
    return parse_json_response("Authorized ✅")

@app.get("/scrapping/status")
def scrapping_status():
    print(SCRAPING_STATUS)
    return SCRAPING_STATUS

@app.post("/scrapping/start")
def start_scrapping(background_tasks: BackgroundTasks):

    init_data()
    time.sleep(1)

    if SCRAPING_STATUS["running"]:
        return parse_json_response("Scraping already running", 409)

    SCRAPING_STATUS.update({
        "running": True,
        "finished": False,
        "current": 0,
        "total": 0,
        "step": "Inicializando",
        "error": None
    })

    # Una única tarea → controla todo el pipeline
    background_tasks.add_task(full_scraping_task)

    return parse_json_response("Scraping started ✅")

@app.get("/files/db")
def list_db_files():
    pattern = f"{INITTED_FOLDER}*_db.*"
    files = glob.glob(pattern)
    return {
        "files": [Path(f).name for f in files]
    }

# ===================
# USERS
# ===================
@app.post("/users/register")
async def register( request: Request, db:SQLiteORM = Depends(get_db) ):

    try:

        json_data = await request.json()
 
        # logging.debug(json_data) 

        username = json_data.get("username", None )
        email = json_data.get("email", None )
        password = json_data.get("password", None )

        if username == None or email == None or password == None:
            return parse_json_response( "Incorrect credentials" , 400 )

        result = db.execute_query(
            """ 
                SELECT * from usuarios where nombre = ? or email = ?
            """,
            ( username, email )
        ).json

        if result:
            return parse_json_response( f"User {username} or email {email} is already taken" , 401 )

        db.execute_query(
            """ 
                INSERT INTO usuarios ( nombre, email , password, rol, token ) VALUES ( ? , ? , ? , ? , ? )
            """,
            ( username , email, password , 'user' , None )
        )

        return parse_json_response("User registered successfully", 200)

    except Exception as e:

        logging.debug(e)
        
        return parse_json_response( str(e) , 400 ) 

@app.post("/users/login")
async def login( request: Request, db: SQLiteORM = Depends(get_db) ):

    try:

        json_data = await request.json()

        # logging.debug(json_data) 

        email = json_data.get("email", None )
        password = json_data.get("password", None )

        if email == None or password == None:
            return parse_json_response( "Incorrect credentials" , 400 )

        result = db.execute_query(
            """ 
                SELECT id_usuario, nombre, email,password from usuarios where email = ?
            """,
            ( email, )
        ).json

        # logging.debug(db.get_query())

        # logging.debug(result) 

        if not result:
            return parse_json_response( f"User {email} does not exist" , 402 )

        password_db = result[0]["password"]
        
        if password_db != password:
            return parse_json_response( "Incorrect password" , 401 )
        
        # To set payload for JWT token
        result = db.execute_query(
            """ 
               SELECT
                    u.id_usuario,
                    u.nombre,
                    u.email,
                    u.rol as role
                from usuarios u
                where u.email = ?
            """,
            ( email, )
        ).json

        # logging.debug(db.get_query())

        import jwt

        # Define a secret key
        secret_key = "secret"

        payload = result[0]
        
        payload["exp"] =  datetime.datetime.utcnow() + datetime.timedelta(hours=1)

        logging.debug(payload)

        encoded_jwt = jwt.encode(payload, secret_key, algorithm="HS256")
        
        db.execute_query(
            """ 
                UPDATE usuarios SET token = ? where email = ?
            """,
            ( encoded_jwt , email )
        )

        return parse_json_response( 
            {
                "token": encoded_jwt
            } 
        )

    except Exception as e:

        logging.debug(e)
        
        return parse_json_response( str(e) , 400 )

# INFO 
# Partidos
@app.get("/info/partidos")
def api_get_partidos( db: SQLiteORM = Depends(get_db) ):
    sql = f"""
        SELECT 
            p.id_partido,
            p.id_temporada,
            p.id_jornada,
            e1.id_equipo as id_equipo_local,
            e2.id_equipo as id_equipo_visitante,
            e1.nombre AS local,
            e2.nombre AS visitante,
            e1.escudo AS escudo_local,
            e2.escudo AS escudo_visitante,
            es.nombre AS estadio,
            p.inicio,
            p.goles_local,
            p.goles_visitante,
            p.estado
        FROM partidos p
        LEFT JOIN equipos e1 ON p.id_local = e1.id_equipo
        LEFT JOIN equipos e2 ON p.id_visitante = e2.id_equipo
        LEFT JOIN estadios es ON p.id_estadio = es.id_estadio
        ORDER BY {date_field("p.inicio")} ASC;
    """

    data = db.execute_query(sql).json
    return {"data": data}

@app.get("/excel/jornadas_liga")
def api_get_jornadas_liga(db: SQLiteORM = Depends(get_db)):

    # =========================
    # CSV
    # =========================
    df = read_file(f"{SCRAPPING_FOLDER}partidos_laliga.csv")

    jornadas_csv = (
        df["Jornada"]
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    jornadas_csv = sorted(jornadas_csv)

    # =========================
    # BD
    # =========================
    sql = """
        SELECT j.id_jornada
        FROM jornadas j
        WHERE j.id_temporada = ?
    """

    rows = db.execute_query(sql, (1,)).json
    jornadas_bd = {row["id_jornada"] for row in rows}

    # =========================
    # FUTURAS = CSV - BD
    # =========================
    jornadas_futuras = [
        j for j in jornadas_csv if j not in jornadas_bd
    ]

    return {
        "jornadas_futuras": jornadas_futuras,
        "ultima_jornada_jugada": max(jornadas_bd) if jornadas_bd else None,
    }

@app.get("/info/jornadas")
def api_get_jornadas(db: SQLiteORM = Depends(get_db)):

    sql = """
        SELECT j.id_jornada
        FROM jornadas j
        WHERE j.id_temporada = ?
    """

    rows = db.execute_query(sql, (1,)).json

    # Extraer ints limpios
    jornadas_bd = [row["id_jornada"] for row in rows]

    return {
        "data": jornadas_bd
    }

# ESTADIOS
# info estadios
@app.get("/info/estadios")
def api_get_estadios( db: SQLiteORM = Depends(get_db) ):
    sql = f"""
        SELECT 
            es.id_estadio,
            es.nombre,
            es.latitud,
            es.longitud,
            es.lugar,
            es.capacidad,
            (select nombre from equipos where id_equipo = es.id_equipo) as equipo
        FROM estadios es
    """

    data = db.execute_query(sql).json
    return {"data": data}

# EQUIPOS
# info equipos
@app.get("/info/equipos")
def api_get_equipos(id: Optional[str] = None, db: SQLiteORM = Depends(get_db)):

    sql = """
        SELECT 
            e.id_equipo,
            (SELECT nombre FROM estadios WHERE id_equipo = e.id_equipo) AS estadio,
            e.nombre,
            e.escudo
        FROM equipos e
        WHERE 1=1
    """

    data = BuildQuery(db, sql)

    return {"data": data}

@app.get("/info/jugadores")
def get_jugadores( id: Optional[str] = None, db: SQLiteORM = Depends(get_db) ):

    sql = """
        SELECT
            j.id_jugador,
            j.nombre,
            ( select nombre_completo from posiciones where j.id_posicion = id_posicion ) as posicion,
            j.edad,
            eq.nombre AS equipo,
            eq.id_equipo,
            eq.escudo
        FROM jugadores j
        LEFT JOIN equipos eq ON j.id_equipo = eq.id_equipo
        WHERE 1 = 1
        ORDER BY j.nombre ASC
    """
    data = BuildQuery(db, sql, filters={"eq.id_equipo":id})
    return {"data": data}


@app.get("/info/estadisticas_jugador")
def get_player_stats(filters: dict, db: SQLiteORM = Depends(get_db)):

    sql = f"""
        SELECT 
            ej.id_partido,
            ej.id_jornada,
            ej.minutesPlayed,
            ej.rating,

            ej.goals,
            ej.expectedGoals,
            ej.expectedAssists,
            ej.totalShots,
            ej.shotOffTarget,

            ej.totalPass,
            ej.accuratePass,
            ej.totalLongBalls,
            ej.accurateLongBalls,

            ej.totalCross,
            ej.accurateOppositionHalfPasses,

            ej.totalTackle,
            ej.wonTackle,
            ej.interceptionWon,
            ej.ballRecovery,

            ej.totalContest,
            ej.duelWon,
            ej.duelLost,
            ej.aerialWon,
            ej.aerialLost,

            ej.wasFouled,
            ej.fouls,
            ej.errorLeadToAShot,
            ej.errorLeadToAGoal

        FROM estadisticas_jugadores ej
        ORDER BY ej.id_jornada ASC
    """

    data = db.execute_query(sql).json
    return {"data": data}

@app.get("/info/clasificaciones/equipos")
def get_teams_rank(id: Optional[str] = None , db: SQLiteORM = Depends(get_db)):

    sql = f"""
        WITH resultados AS (
            -- Local
            SELECT
                p.id_local AS id_equipo,
                CASE
                    WHEN p.goles_local > p.goles_visitante THEN 3
                    WHEN p.goles_local = p.goles_visitante THEN 1
                    ELSE 0
                END AS puntos,
                p.goles_local AS gf,
                p.goles_visitante AS gc,
                CASE WHEN p.goles_local > p.goles_visitante THEN 1 ELSE 0 END AS victorias,
                CASE WHEN p.goles_local = p.goles_visitante THEN 1 ELSE 0 END AS empates,
                CASE WHEN p.goles_local < p.goles_visitante THEN 1 ELSE 0 END AS derrotas
            FROM partidos p

            UNION ALL

            -- Visitante
            SELECT
                p.id_visitante AS id_equipo,
                CASE
                    WHEN p.goles_visitante > p.goles_local THEN 3
                    WHEN p.goles_visitante = p.goles_local THEN 1
                    ELSE 0
                END AS puntos,
                p.goles_visitante AS gf,
                p.goles_local AS gc,
                CASE WHEN p.goles_visitante > p.goles_local THEN 1 ELSE 0 END AS victorias,
                CASE WHEN p.goles_visitante = p.goles_local THEN 1 ELSE 0 END AS empates,
                CASE WHEN p.goles_visitante < p.goles_local THEN 1 ELSE 0 END AS derrotas
            FROM partidos p
        ),

        clasificacion AS (
            SELECT
                e.id_equipo,
                e.nombre AS equipo,
                SUM(r.puntos) AS puntos,
                SUM(r.victorias) AS victorias,
                SUM(r.empates) AS empates,
                SUM(r.derrotas) AS derrotas,
                SUM(r.gf) AS goles_favor,
                SUM(r.gc) AS goles_contra,
                SUM(r.gf) - SUM(r.gc) AS diferencia_goles,
                RANK() OVER (
                    ORDER BY
                        SUM(r.puntos) DESC,
                        (SUM(r.gf) - SUM(r.gc)) DESC,
                        SUM(r.gf) DESC,
                        SUM(r.gc) ASC
                ) AS posicion
            FROM resultados r
            JOIN equipos e ON e.id_equipo = r.id_equipo
            GROUP BY e.id_equipo, e.nombre
        )

        SELECT *
        FROM clasificacion
        ORDER BY puntos DESC, diferencia_goles DESC, goles_favor DESC, goles_contra ASC
    """

    data = BuildQuery(db, sql)
    return {"data": data}

@app.get("/info/clasificaciones/jugadores")
def get_players_by_goal_rank(by: str = "goals" , db: SQLiteORM = Depends(get_db)):

    sqls = {
        "goals": """
            SELECT
                *,
                RANK() OVER (
                    ORDER BY goles DESC, minutos ASC, asistencias DESC, partidos ASC
                ) AS posicion
            FROM (
                SELECT
                    j.id_jugador,
                    j.nombre AS jugador,
                    e.nombre AS equipo,
                    SUM(js.goals) AS goles,
                    SUM(js.goalAssist) AS asistencias,
                    SUM(js.minutesPlayed) AS minutos,
                    COUNT(js.id_partido) AS partidos
                FROM jugadores_stats js
                JOIN jugadores j ON j.id_jugador = js.id_jugador
                JOIN equipos e ON e.id_equipo = js.id_equipo
                GROUP BY j.id_jugador, j.nombre, e.nombre
            )
            ORDER BY goles DESC, minutos ASC, asistencias DESC, partidos ASC
        """,

        "minutes": """
            SELECT
                *,
                RANK() OVER (ORDER BY minutos DESC) AS posicion
            FROM (
                SELECT
                    j.id_jugador,
                    j.nombre AS jugador,
                    e.nombre AS equipo,
                    SUM(js.minutesPlayed) AS minutos
                FROM jugadores_stats js
                JOIN jugadores j ON j.id_jugador = js.id_jugador
                JOIN equipos e ON e.id_equipo = js.id_equipo
                GROUP BY j.id_jugador, j.nombre, e.nombre
            )
            ORDER BY minutos DESC
        """,

        "matches": """
            SELECT
                *,
                RANK() OVER (ORDER BY partidos DESC) AS posicion
            FROM (
                SELECT
                    j.id_jugador,
                    j.nombre AS jugador,
                    e.nombre AS equipo,
                    COUNT(js.id_partido) AS partidos
                FROM jugadores_stats js
                JOIN jugadores j ON j.id_jugador = js.id_jugador
                JOIN equipos e ON e.id_equipo = js.id_equipo
                GROUP BY j.id_jugador, j.nombre, e.nombre
            )
            ORDER BY partidos DESC
        """,

        "position": """
            SELECT
                *,
                RANK() OVER (ORDER BY asistencias DESC) AS posicion
            FROM (
                SELECT
                    j.id_jugador,
                    j.nombre AS jugador,
                    e.nombre AS equipo,
                    SUM(js.goalAssist) AS asistencias
                FROM jugadores_stats js
                JOIN jugadores j ON j.id_jugador = js.id_jugador
                JOIN equipos e ON e.id_equipo = js.id_equipo
                GROUP BY j.id_jugador, j.nombre, e.nombre
            )
            ORDER BY asistencias DESC
        """
    }

    # Asegurar que existe la consulta
    sql = sqls.get(by, sqls["goals"])

    # EJECUCIÓN CORRECTA
    data = BuildQuery(db, sql)

    return {"data": data}


# Machine learning
@app.post("/ml/forecasting/score")
def ml_predict_score(): 
    
    try:

        return { "data": predict()["simulaciones_futuras"] } 

    except Exception as e:

        return parse_json_response( str(e) , 400 )



# Dashboard

# ============================
# KPIS
# ============================
from fastapi import Depends
from collections import defaultdict
from math import ceil

@app.get("/dashboard/kpis-equipo/{id_equipo}")
def kpis_equipo(id_equipo: int, db: SQLiteORM = Depends(get_db)):

    # =========================
    # KPI BÁSICOS
    # =========================
    stats = db.execute_query("""
        SELECT
            COUNT(*) AS partidos,

            SUM(
                CASE
                    WHEN id_local = ? THEN goles_local
                    ELSE goles_visitante
                END
            ) AS goles_favor,

            SUM(
                CASE
                    WHEN id_local = ? THEN goles_visitante
                    ELSE goles_local
                END
            ) AS goles_contra,

            SUM(
                CASE
                    WHEN (id_local = ? AND goles_local > goles_visitante)
                      OR (id_visitante = ? AND goles_visitante > goles_local)
                        THEN 3
                    WHEN goles_local = goles_visitante THEN 1
                    ELSE 0
                END
            ) AS puntos

        FROM partidos
        WHERE id_local = ? OR id_visitante = ?
    """, (
        id_equipo,
        id_equipo,
        id_equipo,
        id_equipo,
        id_equipo,
        id_equipo,
    )).json

    if not stats:
        return {
            "ppg": 0,
            "diferencia_goles": 0,
            "goles_favor_partido": 0,
            "kd_variacion": []
        }

    partidos = stats[0]["partidos"] or 1
    goles_favor = stats[0]["goles_favor"] or 0
    goles_contra = stats[0]["goles_contra"] or 0
    puntos = stats[0]["puntos"] or 0

    ppg = round(puntos / partidos, 2)
    diferencia_goles = goles_favor - goles_contra
    goles_favor_partido = round(goles_favor / partidos, 2)

    # =========================
    # KD POR JORNADAS
    # =========================
    jornadas = db.execute_query("""
        SELECT
            id_jornada,

            SUM(
                CASE
                    WHEN id_local = ? THEN goles_local
                    ELSE goles_visitante
                END
            ) AS gf,

            SUM(
                CASE
                    WHEN id_local = ? THEN goles_visitante
                    ELSE goles_local
                END
            ) AS gc

        FROM partidos
        WHERE id_local = ? OR id_visitante = ?
        GROUP BY id_jornada
        ORDER BY id_jornada DESC
        LIMIT 2
    """, (
        id_equipo,
        id_equipo,
        id_equipo,
        id_equipo,
    )).json

    kd_variacion = []

    if jornadas:
        actual = jornadas[0]
        anterior = jornadas[1] if len(jornadas) > 1 else None

        kd_actual = round((actual["gf"] + 1) / (actual["gc"] + 1), 2)

        if anterior:
            kd_anterior = round((anterior["gf"] + 1) / (anterior["gc"] + 1), 2)
        else:
            kd_anterior = kd_actual

        porcentaje = (
            round(((kd_actual - kd_anterior) / kd_anterior) * 100, 2)
            if kd_anterior != 0 else 0
        )

        kd_variacion.append({
            "id_jornada_actual": actual["id_jornada"],
            "id_jornada_anterior": anterior["id_jornada"] if anterior else actual["id_jornada"],
            "kd_jornada_actual": kd_actual,
            "kd_jornada_anterior": kd_anterior,
            "porcentaje": porcentaje
        })

    # =========================
    # RESPUESTA FINAL
    # =========================
    return {
        "ppg": ppg,
        "diferencia_goles": diferencia_goles,
        "goles_favor_partido": goles_favor_partido,
        "kd_variacion": kd_variacion
    }


@app.get("/dashboard/kpis")
def dashboard_kpis(db: SQLiteORM = Depends(get_db)):

    try:

        # ============================
        # 1️⃣ KPIs GENERALES
        # ============================

        total_equipos = db.execute_query("""
            SELECT COUNT(*) AS total
            FROM equipos
        """).json[0]["total"]

        promedio_goles = db.execute_query("""
            SELECT ROUND(AVG(goles_local + goles_visitante), 2) AS promedio
            FROM partidos
        """).json[0]["promedio"]

        total_gastos = db.execute_query("""
            SELECT
                ROUND(SUM(j.precio) / 1000000.0, 2) AS total_millones
            FROM jugadores j
        """).json[0]["total_millones"]

        # ============================
        # 2️⃣ GOLES A FAVOR / EN CONTRA
        # ============================

        goles_stats = db.execute_query("""
            SELECT
                ROUND(AVG(goles_local), 2) AS goles_local,
                ROUND(AVG(goles_visitante), 2) AS goles_visitante
            FROM partidos
        """).json[0]

        goles_favor_partido = goles_stats["goles_local"]
        goles_contra_partido = goles_stats["goles_visitante"]
        diferencia_goles = round(goles_favor_partido - goles_contra_partido, 2)

        # ============================
        # 3️⃣ PPG – PUNTOS POR PARTIDO
        # ============================

        ppg = db.execute_query("""
            SELECT ROUND(AVG(puntos), 2) AS ppg
            FROM (
                SELECT
                    CASE
                        WHEN goles_local > goles_visitante THEN 3
                        WHEN goles_local = goles_visitante THEN 1
                        ELSE 0
                    END AS puntos
                FROM partidos
            )
        """).json[0]["ppg"]

        # ============================
        # 4️⃣ DEPENDENCIA OFENSIVA
        # ============================

        dependencia = db.execute_query("""
            WITH goles_jugador AS (
                SELECT
                    id_jugador,
                    SUM(goals) AS total_goles
                FROM jugadores_stats
                GROUP BY id_jugador
            )
            SELECT
                MAX(total_goles) * 1.0 / SUM(total_goles) AS dependencia
            FROM goles_jugador
        """).json[0]["dependencia"]

        dependencia_pct = round((dependencia or 0) * 100, 2)

        # ============================
        # 5️⃣ ÚLTIMAS 5 JORNADAS
        # ============================

        ultimos_5 = db.execute_query("""
            SELECT SUM(puntos) AS puntos_5
            FROM (
                SELECT
                    CASE
                        WHEN goles_local > goles_visitante THEN 3
                        WHEN goles_local = goles_visitante THEN 1
                        ELSE 0
                    END AS puntos
                FROM partidos
                ORDER BY id_jornada DESC
                LIMIT 5
            )
        """).json[0]["puntos_5"]

        # ============================
        # 6️⃣ POSICIÓN ACTUAL (LIGA)
        # ============================

        posicion_actual = db.execute_query("""
            WITH puntos_acumulados AS (
                SELECT
                    e.nombre AS equipo,
                    SUM(
                        CASE
                            WHEN p.id_local = e.id_equipo AND p.goles_local > p.goles_visitante THEN 3
                            WHEN p.id_visitante = e.id_equipo AND p.goles_visitante > p.goles_local THEN 3
                            WHEN p.goles_local = p.goles_visitante THEN 1
                            ELSE 0
                        END
                    ) AS puntos
                FROM equipos e
                JOIN partidos p
                ON e.id_equipo IN (p.id_local, p.id_visitante)
                GROUP BY e.id_equipo
            )
            SELECT
                RANK() OVER (ORDER BY puntos DESC) AS posicion
            FROM puntos_acumulados
            LIMIT 1
        """).json[0]["posicion"]

        # ============================
        # 7️⃣ KD (YA LO TENÍAS)
        # ============================

        kd_variacion = db.execute_query("""
            WITH stats_por_jornada AS (
                SELECT
                    id_jornada,

                    COUNT(*) AS partidos,

                    SUM(
                        CASE
                            WHEN goles_local <> goles_visitante THEN 1
                            ELSE 0
                        END
                    ) AS victorias,

                    SUM(
                        CASE
                            WHEN goles_local = goles_visitante THEN 1
                            ELSE 0
                        END
                    ) AS empates

                FROM partidos
                GROUP BY id_jornada
            ),

            kd_por_jornada AS (
                SELECT
                    id_jornada,
                    ROUND(
                        (victorias + empates * 0.5) / NULLIF(partidos, 0),
                        4
                    ) AS kd
                FROM stats_por_jornada
            ),

            kd_variacion AS (
                SELECT
                    id_jornada                                    AS id_jornada_actual,
                    kd                                            AS kd_jornada_actual,
                    LAG(id_jornada) OVER (ORDER BY id_jornada)   AS id_jornada_anterior,
                    LAG(kd) OVER (ORDER BY id_jornada)           AS kd_jornada_anterior,
                    ROUND(
                        (kd - LAG(kd) OVER (ORDER BY id_jornada)) * 100.0 /
                        NULLIF(LAG(kd) OVER (ORDER BY id_jornada), 0),
                        2
                    ) AS porcentaje
                FROM kd_por_jornada
            )

            SELECT *
            FROM kd_variacion
            ORDER BY id_jornada_actual DESC
            LIMIT 1


        """).json

        # ============================
        # 📦 RESPUESTA FINAL
        # ============================

        return {
            "total_equipos": total_equipos,              # (opcional, puedes ocultarlo)
            "total_gastos": total_gastos,              # (opcional, puedes ocultarlo)
            "promedio_goles": promedio_goles,            # (opcional)
            "ppg": ppg,
            "goles_favor_partido": goles_favor_partido,
            "goles_contra_partido": goles_contra_partido,
            "diferencia_goles": diferencia_goles,
            "dependencia_ofensiva_pct": dependencia_pct,
            "puntos_ultimas_5": ultimos_5,
            "posicion_actual": posicion_actual,
            "kd_variacion": kd_variacion
        }

    except Exception as e:
        return parse_json_response(str(e), 400)

@app.get("/dashboard/goles-jugador/{id_equipo}")
def goles_por_jugador(id_equipo: int, db: SQLiteORM = Depends(get_db)):

    rows = db.execute_query(
        """
        SELECT
            js.id_jugador,
            (SELECT nombre FROM jugadores WHERE id_jugador = js.id_jugador) AS jugador,
            ROUND(SUM(js.goals), 2) AS total_goals
        FROM jugadores_stats js
        WHERE js.id_equipo = ?
        GROUP BY js.id_jugador
        ORDER BY 3 DESC
        """,
        (id_equipo,)
    ).json

    return rows

@app.get("/dashboard/stats-jugador")
def stats_por_jugador( stat:str, id_equipo:int , db: SQLiteORM = Depends(get_db)):

    stat_expr = f"ROUND(SUM(s.{stat}), 2)"

    if stat == "rating":
        stat_expr = f"ROUND(SUM(s.{stat}), 0)"

    rows = db.execute_query(
        f"""
        SELECT 
            j.nombre as nombre_jugador, 
            ( select nombre_completo from posiciones where id_posicion = j.id_posicion ) as posicion, 
            {stat_expr} AS valor,
            CAST(SUM(s.minutesPlayed) AS INTEGER) AS minutos,
            ROUND(AVG(s.rating), 2) AS rating_promedio
        FROM jugadores_stats s
        JOIN jugadores j ON s.id_jugador = j.id_jugador
        JOIN equipos e ON s.id_equipo = e.id_equipo
        WHERE e.id_equipo = ? AND s.rating > 0
        GROUP BY j.id_jugador, j.nombre, e.nombre
        ORDER BY valor DESC
        LIMIT ?
        """,
        (id_equipo,10,)
    ).json

    return rows

@app.get("/dashboard/bumpy-clasificacion/{id_equipo}")
def bumpy_clasificacion(id_equipo: int, db: SQLiteORM = Depends(get_db)):

    rows = db.execute_query("""
        WITH resultados AS (
            SELECT
                p.id_jornada,
                e.id_equipo,
                e.nombre AS equipo,
                CASE
                    WHEN p.id_local = e.id_equipo THEN p.goles_local
                    ELSE p.goles_visitante
                END AS goles_favor,
                CASE
                    WHEN p.id_local = e.id_equipo THEN p.goles_visitante
                    ELSE p.goles_local
                END AS goles_contra
            FROM partidos p
            JOIN equipos e
              ON e.id_equipo IN (p.id_local, p.id_visitante)
        ),
        puntos AS (
            SELECT
                id_jornada,
                id_equipo,
                equipo,
                CASE
                    WHEN goles_favor > goles_contra THEN 3
                    WHEN goles_favor = goles_contra THEN 1
                    ELSE 0
                END AS puntos
            FROM resultados
        ),
        acumulado AS (
            SELECT
                id_jornada,
                id_equipo,
                equipo,
                SUM(puntos) OVER (
                    PARTITION BY id_equipo
                    ORDER BY id_jornada
                ) AS puntos_acumulados
            FROM puntos
        )
        SELECT
            id_jornada,
            id_equipo,
            equipo,
            RANK() OVER (
                PARTITION BY id_jornada
                ORDER BY puntos_acumulados DESC
            ) AS posicion
        FROM acumulado
        ORDER BY equipo, id_jornada
    """).json

    # 🔹 Equipo seleccionado
    selected_team = next(
        (r["equipo"] for r in rows if r["id_equipo"] == id_equipo),
        None
    )

    team_positions = defaultdict(list)
    team_colors = {}

    for r in rows:
        equipo = r["equipo"]

        team_positions[equipo].append(r["posicion"])

        # 🔹 Color generado UNA sola vez por equipo
        if equipo not in team_colors:
            team_colors[equipo] = color_from_name(equipo)

    return {
        "selected_team": selected_team,
        "data": dict(team_positions),
        "colors": team_colors
    }

@app.get("/dashboard/ranking-paradas-porteros/{id_equipo}")
def top_saves_goalkeepers( id_equipo:int, db:SQLiteORM = Depends(get_db) ):

    return db.execute_query(
        """
        SELECT
            j.id_jugador,
            j.nombre AS jugador,
            e.nombre AS equipo,
            SUM(js.saves) AS total_paradas,
            COUNT(js.id_partido) AS partidos,
            ROUND(
                CAST(SUM(js.saves) AS FLOAT) / NULLIF(COUNT(js.id_partido), 0),
                2
            ) AS paradas_por_partido
        FROM jugadores_stats js
        JOIN jugadores j ON j.id_jugador = js.id_jugador
        JOIN equipos e ON e.id_equipo = j.id_equipo
        WHERE ( select nombre from posiciones where id_posicion = j.id_posicion ) = 'G'
        GROUP BY j.id_jugador, j.nombre, e.nombre
        ORDER BY total_paradas DESC
        LIMIT 20

        """
    ).json

@app.get("/dashboard/ranking-value-market-players/{id_equipo}")
def top_sold_players( id_equipo:int, db:SQLiteORM = Depends(get_db) ):

    return db.execute_query(
        """
        SELECT
            j.id_jugador,
            j.nombre AS jugador,
            ( select nombre_completo from posiciones where id_posicion = j.id_posicion ) as posicion,
            e.nombre AS equipo,
            ( '€' || ROUND(j.precio / 1000000.0, 2) || ' M' ) AS precio
        FROM jugadores j
        JOIN equipos e ON e.id_equipo = j.id_equipo
        WHERE j.precio IS NOT NULL
        ORDER BY j.precio DESC
        LIMIT 25

        """
    ).json

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
import glob
from pathlib import Path 
import time
import datetime
import random
import requests
from typing import Optional
from helpers.sofa_utils import read_file
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
            ( select nombre from posiciones where j.id_posicion = id_posicion ) as posicion,
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
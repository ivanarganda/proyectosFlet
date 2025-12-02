import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "DatabaseORM"))
from DatabaseORM.SQLiteORM import *
import re
import requests
from datetime import datetime
import time

db = SQLiteORM("futbol.db")

db.connect_DB()

def drop_all_tables():

    try:

        tables = [ table.get("name") for table in db.get_db_tables() if table.get("name") != "sqlite_sequence"]

        if not tables:

            raise Exception("Not found database tables")

        db.drop_tables( list(tables) )

    except Exception as e:

        print(e)


def drop_tables(tables: list) -> bool:

    try:

        if not tables:

            raise Exception("Empty list of tables")

        db.drop_tables(tables)

    except Exception as e:

        print(e)
    
def init_tables():

    db.create_tables({

        # ============================================================
        # TEMPORADAS
        # ============================================================
        "temporadas": [
            {
                "id_temporada": integer(autoincrement=True),
                "nombre": text(not_null=True),
                "year_start": integer(),
                "year_end": integer(),
                "id_liga": integer(default=8),
                "fecha_creacion": numeric(default=db.date())
            }
        ],

        # ============================================================
        # EQUIPOS
        # ============================================================
        "equipos": [
            {
                "id_equipo": integer(primary_key=True),
                "nombre": text(not_null=True),
                "slug": text(),
                "escudo": text()
            }
        ],

        # ============================================================
        # ESTADIOS
        # ============================================================
        "estadios": [
            {
                "id_estadio": integer(primary_key=True),
                "nombre": text(not_null=True),
                "ciudad": text(),
                "capacidad": integer(),
                "id_equipo": integer()
            },
            {
                "fk_estadios_equipos": ("id_equipo", "equipos", "id_equipo")
            }
        ],

        # ============================================================
        # JORNADAS
        # ============================================================
        "jornadas": [
            {
                "id_jornada": integer(autoincrement=True),
                "id_temporada": integer(not_null=True),
                "numero": integer(not_null=True),
                "fecha_creacion": numeric(default=db.date())
            },
            {
                "fk_jornadas_temporadas":("id_temporada", "temporadas", "id_temporada"),
            }
        ],

        # ============================================================
        # PARTIDOS
        # ============================================================
        "partidos": [
            {
                "id_partido": integer(primary_key=True),
                "id_temporada": integer(not_null=True),
                "id_jornada": integer(not_null=True),
                "id_local": integer(not_null=True),
                "id_visitante": integer(not_null=True),
                "id_estadio": integer(not_null=True),
                "inicio": integer(),
                "estado": text(),
                "goles_local": integer(default=0),
                "goles_visitante": integer(default=0)
            }, 
            {
                "fk_partidos_temporadas": ("id_temporada", "temporadas", "id_temporada"),
                "fk_partidos_jornadas": ("id_jornada", "jornadas", "id_jornada"),
                "fk_partidos_equipos_local": ("id_local", "equipos", "id_equipo"),
                "fk_partidos_equipos_visitante": ("id_visitante", "equipos", "id_equipo"),
                "fk_partidos_estadio": ("id_estadio", "estadios", "id_estadio"),
            }
        ],

        # ============================================================
        # STAT EQUIPO PARTIDO
        # ============================================================
        "stats_equipo_partido": [
            {
                "id_stats": integer(autoincrement=True),
                "id_partido": integer(not_null=True),
                "id_equipo": integer(not_null=True),
                "posesion": real(),
                "tiros_total": integer(),
                "tiros_puerta": integer(),
                "xg": real(),
                "pases": integer(),
                "faltas": integer(),
                "tarjetas_amarillas": integer(),
                "tarjetas_rojas": integer()
            },
            {
                "fk_stats_equipo_partido_partidos": ("id_partido", "partidos", "id_partido"),
                "fk_stats_equipo_partido_equipos": ("id_equipo", "equipos", "id_equipo")
            }
        ],

        # ============================================================
        # STAT JUGADOR PARTIDO
        # ============================================================
        "stats_jugador_partido": [
            {
                "id_registro": integer(autoincrement=True),
                "id_partido": integer(not_null=True),
                "id_jugador": integer(not_null=True),
                "minutos_jugados": real(),
                "goles": integer(),
                "asistencias": integer(),
                "tiros": integer(),
                "tiros_puerta": integer(),
                "xg": real(),
                "pases": integer(),
                "pases_clave": integer(),
                "regates": integer(),
                "duelos_ganados": integer(),
                "valoracion": real()
            },
            {
                "fk_stats_jugador_partido_partidos": ("id_partido", "partidos","id_partido"),
            }
        ],

        # ============================================================
        # USUARIOS
        # ============================================================
        "usuarios": [
            {
                "id_usuario": integer(autoincrement=True),
                "nombre": text(not_null=True),
                "email": text(not_null=True),
                "password": text(not_null=True),
                "rol": enum(enum_values=["user","admin"],default="user"),
                "fecha_registro": numeric(default=db.date())
            }
        ],

        # ============================================================
        # REPORTES
        # ============================================================
        "reportes": [
            {
                "id_reporte": integer(autoincrement=True),
                "id_usuario": integer(not_null=True),
                "titulo": text(not_null=True),
                "descripcion": text(),
                "fecha_creacion": numeric(default=db.date())
            },
            {
                "fk_reportes_usuarios": ("id_usuario", "usuarios","id_usuario"),
            }
        ],

        # ============================================================
        # REPORTES_PARTIDOS
        # ============================================================
        "reportes_partidos": [
            {
                "id": integer(autoincrement=True),
                "id_reporte": integer(not_null=True),
                "id_partido": integer(not_null=True),
                "comentario": text()
            },
            {
                "fk_reportes_partidos_reportes": ("id_reporte", "reportes","id_reporte"),
                "fk_reportes_partidos_partidos": ("id_partido", "partidos","id_partido")
            }
        ],

        # ============================================================
        # REPORTES_JUGADORES
        # ============================================================
        "reportes_jugadores": [
            {
                "id": integer(autoincrement=True),
                "id_reporte": integer(not_null=True),                
                "id_jugador": integer(not_null=True),               
                "comentario": text()
            },
            {
                "fk_reportes_jugadores_reportes":("id_reporte", "reportes","id_reporte")
            }
        ]

    })

drop_all_tables()
time.sleep(1)
init_tables()
import os
import sys
from ivbox.SQLiteORM import *
import re
import requests
from datetime import datetime
import time
from params import DB

def init_tables():

    db = SQLiteORM(DB)

    db.connect_DB()

    def drop_all_tables(exceptions: list=[]) -> bool:

        try:

            tables = [ table.get("name") for table in db.get_db_tables() if table.get("name") != "sqlite_sequence"]

            if not tables:

                raise Exception("Not found database tables")

            db.drop_tables( list(tables) )

            return True

        except Exception as e:

            print(e)

            return False


    def drop_tables(tables: list) -> bool:

        try:

            if not tables:

                raise Exception("Empty list of tables")

            db.drop_tables(tables)

        except Exception as e:

            print(e)
        
    def playload_tables():

        db.create_tables({

            "temporadas": [
                {
                    "id_temporada": integer(pk=True),
                    "nombre": text(not_null=True),
                    "year_start": integer(),
                    "year_end": integer(),
                    "id_liga": integer(default=8),
                    "fecha_creacion": numeric(default=db.date())
                }
            ],

            "equipos": [
                {
                    "id_equipo": integer(pk=True),
                    "nombre": text(not_null=True),
                    "slug": text(),
                    "escudo": text()
                }
            ],

            "posiciones": [
                {
                    "id_posicion": integer(pk=True),
                    "nombre": text(not_null=True)
                }
            ],

            "jugadores": [
                {
                    "id_jugador": text(pk=True),
                    "nombre": text(default="Unknown"),
                    "edad": integer(not_null=True),
                    "sexo": enum(enum_values=["M","F"], not_null=True),
                    "id_posicion": integer(not_null=True),
                    "id_equipo": integer(not_null=True)
                },
                {
                    "fk_jugadores_equipos": ("id_equipo", "equipos", "id_equipo"),
                    "fk_jugadores_posiciones": ("id_posicion", "posiciones", "id_posicion"),
                }
            ],

            "estadios": [
                {
                    "id_estadio": integer(pk=True),
                    "nombre": text(not_null=True),
                    "latitud": text(),
                    "longitud": text(),
                    "capacidad": integer(),
                    "id_equipo": integer()
                },
                {
                    "fk_estadios_equipos": ("id_equipo", "equipos", "id_equipo")
                }
            ],


            "jornadas": [
                {
                    "id_jornada": integer(pk=True,not_null=True),
                    "id_temporada": integer(not_null=True),
                    "fecha_creacion": numeric(default=db.datetime())
                },
                {
                    "fk_jornadas_temporadas":("id_temporada", "temporadas", "id_temporada"),
                }
            ],

            "partidos": [
                {
                    "id_partido": integer(pk=True),
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

            "jugadores_stats": [
                {
                    "id_estadistica_jugadores": integer(pk=True),
                    "id_jugador": text(not_null=True),
                    "id_equipo": integer(not_null=True),
                    "id_partido": integer(not_null=True),
                    "id_jornada": integer(),
                    "minutesPlayed": real(),
                    "rating": real(),
                    "touches": integer(),
                    "position": text(),
                    "saves": integer(),
                    "penaltySave": integer(),
                    "goals": integer(),
                    "expectedGoals": real(),
                    "totalShots": integer()
                },
                {
                    "fk_stats_jugador_partido_jugadores": ("id_jugador", "jugadores", "id_jugador"),
                    "fk_stats_jugador_partido_partidos": ("id_partido", "partidos", "id_partido")
                }
            ],

            "usuarios": [
                {
                    "id_usuario": integer(pk=True),
                    "nombre": text(not_null=True),
                    "email": text(not_null=True),
                    "password": text(not_null=True),
                    "rol": enum(enum_values=["user","admin"],default="user"),
                    "token": text(),
                    "fecha_registro": numeric(default=db.date())
                }
            ],

            "reportes": [
                {
                    "id_reporte": integer(pk=True),
                    "id_usuario": integer(not_null=True),
                    "titulo": text(not_null=True),
                    "descripcion": text(),
                    "filtros": obj(default="""{}"""),
                    "fecha_creacion": numeric(default=db.date())
                },
                {
                    "fk_reportes_usuarios": ("id_usuario", "usuarios","id_usuario"),
                }
            ],

            "reportes_partidos": [
                {
                    "id": integer(pk=True),
                    "id_reporte": integer(not_null=True),
                    "id_partido": integer(not_null=True),
                    "comentario": text()
                },
                {
                    "fk_reportes_partidos_reportes": ("id_reporte", "reportes","id_reporte"),
                    "fk_reportes_partidos_partidos": ("id_partido", "partidos","id_partido")
                }
            ],

            "reportes_jugadores": [
                {
                    "id": integer(pk=True),
                    "id_reporte": integer(not_null=True),                
                    "id_jugador": text(not_null=True),               
                    "comentario": text()
                },
                {
                    "fk_reportes_jugadores_reportes":("id_reporte", "reportes","id_reporte")
                }
            ]

        })

    drop_all_tables(exceptions=["usuarios", "reportes","reportes_jugadores","reportes_partidos"])
    time.sleep(1)
    playload_tables()

    db.execute_query(
        "VACUUM"
    )

    user_admin = os.getenv("ADMIN_USER")
    email_admin = os.getenv("ADMIN_EMAIL")
    password_admin = os.getenv("PASSWORD_USER")

if __name__ == "__main__":
    init_tables()
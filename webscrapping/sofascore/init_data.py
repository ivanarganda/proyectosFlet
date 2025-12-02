import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "DatabaseORM"))
from DatabaseORM.SQLiteORM import *
import re
import requests
from datetime import datetime
import json

db = SQLiteORM("futbol.db")

db.connect_DB()

def drop_tables():

    db.drop_tables([
       "usuarios",
       "temporadas",
       "equipos",
       "partidos",
       "stats_equipo_partido",
       "reportes"
    ])

def init_tables():

    db.create_tables({

        "usuarios": [
            {
                "id_usuario": integer(not_null=True,autoincrement=True),
                "nombre": text( not_null=True ),
                "email": text( unique=True, not_null=True ),
                "password": text( not_null=True ),
                "created_at": numeric( default=db.datetime() ),
                "updated_at": numeric( default=db.datetime())
            }
        ],
        # ============================================================
        # 1. TEMPORADAS
        # ============================================================
        "temporadas": [
            {
                "id_temporada": integer(autoincrement=True),
                "nombre": text(not_null=True),        # "2024/2025"
                "fecha_inicio": numeric(default=db.date()),
                "fecha_fin": numeric(default=db.date())
            }
        ],

        # ============================================================
        # 2. EQUIPOS
        # ============================================================
        "equipos": [
            {
                "id_equipo": integer(autoincrement=True),
                "nombre": text(not_null=True),        # "Real Madrid"
                "abreviatura": text(),                # "RMA"
                "ciudad": text()
            }
        ],

        "estadios": [
            {
                "id_estadio": integer(autoincrement=True),
                "nombre": text(not_null=True),        # "Real Madrid"
                "abreviatura": text(),                # "RMA"
                "ciudad": text()
            }
        ],
        # ============================================================
        # 3. PARTIDOS
        # ============================================================
        "partidos": [
            {
                "id_partido": integer(primary_key=True),
                "id_temporada": integer(not_null=True),
                "ronda": integer(not_null=True),
                "fecha": text(not_null=True),
                "id_estadio_dentro": integer(not_null=True),
                "goles_dentro": integer(),
                "id_estadio_fuera": integer(not_null=True),
                "goles_fuera": integer(),
                "estado": text(not_null=True),
                "slug": text(),
                "timestamp_raw": integer()
            },
            {
                "fk_temporada": ("id_temporada", "temporadas", "id_temporada"),
                "fk_estadio_partido": ( ("id_estadio_dentro","id_estadio_fuera") , "estadios" , ("id_estadio_dentro","id_estadio_fuera") )
            }
        ],

        "reportes": [
            {
                "id_reporte": integer( autoincrement=True ),
                "titulo": text( not_null=True ),
                "filtros": obj( not_null=True ),
                "id_usuario": integer(not_null=True),
                "created_at": numeric( default=db.datetime() ),
                "updated_at": numeric( default=db.datetime() )
            },
            {
                "fk_reportes_usuarios": ( "id_usuario", "usuarios" , "id_usuario" )
            }
        ]
    })
import os
import sys
from SQLiteORM import *
import re
import requests
from datetime import datetime
import json

db = SQLiteORM("futbol.db")

db.connect_DB()

# db.drop_tables([
#    "temporadas",
#    "equipos",
#    "partidos",
#    "stats_equipo_partido"
# ])

# db.create_tables({

#     # ============================================================
#     # 1. TEMPORADAS
#     # ============================================================
#     "temporadas": [
#         {
#             "id_temporada": integer(autoincrement=True),
#             "nombre": text(not_null=True),        # "2024/2025"
#             "fecha_inicio": numeric(default=db.date()),
#             "fecha_fin": numeric(default=db.date())
#         }
#     ],

#     # ============================================================
#     # 2. EQUIPOS
#     # ============================================================
#     "equipos": [
#         {
#             "id_equipo": integer(autoincrement=True),
#             "nombre": text(not_null=True),        # "Real Madrid"
#             "abreviatura": text(),                # "RMA"
#             "ciudad": text()
#         }
#     ],

#     # ============================================================
#     # 3. PARTIDOS
#     # ============================================================
#     "partidos": [
#         {
#             "id_partido": integer(autoincrement=True),
#             "id_temporada": integer(not_null=True),
#             "jornada": integer(),
#             "fecha": numeric(default=db.datetime()),

#             "id_local": integer(not_null=True),
#             "id_visitante": integer(not_null=True),

#             "goles_local": integer(),
#             "goles_visitante": integer()
#         },
#         {
#             "fk_temporada": ("id_temporada", "temporadas", "id_temporada"),
#             "fk_local": ("id_local", "equipos", "id_equipo"),
#             "fk_visitante": ("id_visitante", "equipos", "id_equipo")
#         }
#     ],

#     # ============================================================
#     # 4. STATS DE EQUIPO POR PARTIDO
#     # ============================================================
#     "stats_equipo_partido": [
#         {
#             "id_stat": integer(autoincrement=True),

#             "id_partido": integer(not_null=True),
#             "id_equipo": integer(not_null=True),

#             "posesion": real(),
#             "tiros_totales": integer(),
#             "tiros_puerta": integer(),
#             "corners": integer(),
#             "faltas": integer(),
#             "xG": real()
#         },
#         {
#             "fk_partido": ("id_partido", "partidos", "id_partido"),
#             "fk_equipo": ("id_equipo", "equipos", "id_equipo")
#         }
#     ]
# })


# ===========================================
# Obtener temporada actual
# ===========================================
def obtener_temporadas_laliga():
    url = "https://api.sofascore.com/api/v1/unique-tournament/8/seasons"
    data = requests.get(url).json()

    temporadas = data.get("seasons", [])

    resultado = []
    for t in temporadas:
        resultado.append({
            "id": t["id"],
            "nombre": t["name"]
        })

    return resultado


# Probarlo
for temp in obtener_temporadas_laliga():
    print(temp)
import requests
import json
from params import *

selected_equipo_id = 24264
kpi_mode = "global"
selected_stat = "totalPass"

def check_saved_filters( id_user, id_report ):

    r = requests.get(f"{REQUEST_URL}/reports_saved/{id_user}/{id_report}").json()

    filtros = json.loads(r[0].get("filtros"))

    return filtros.get("team_id") , filtros.get("kpi_mode") , filtros.get("stat")

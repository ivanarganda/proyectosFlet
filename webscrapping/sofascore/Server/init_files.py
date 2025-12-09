from helpers.sofa_utils import *
import pandas as pd
import numpy as np
from params import *
from datetime import datetime
from helpers.player_stats_fields import PLAYER_STATS_FIELDS
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
warnings.filterwarnings("ignore", category=UserWarning, module="pandas")

def run_init_files( progress_cb = None ):

    TOTAL_STEPS = 6
    current_step = 0

    def update(step_name):
        nonlocal current_step
        current_step += 1
        if progress_cb:
            progress_cb(step_name, current_step, TOTAL_STEPS)

    scraping_folder = SCRAPPING_FOLDER

    # ==========================================================
    # 1. CARGA DE FICHEROS BASE
    # ==========================================================
    update("Cargando ficheros base")
    path_jornadas_info = f"{scraping_folder}jornadas_00_14_info.xlsx"
    path_estadisticas_jugadores_por_jornada = f"{scraping_folder}estadisticas_jugadores_por_jornada_01_14.xlsx"

    new_path_folder_partidos_info = combine_sheets_with_one(current_path=path_jornadas_info, new_file="partidos_info")
    new_path_folder_jugadores_stats = combine_sheets_with_one(current_path=path_estadisticas_jugadores_por_jornada, new_file="jugadores_stats")

    df_partidos_info = read_file(new_path_folder_partidos_info)
    df_jugadores_stats = read_file(new_path_folder_jugadores_stats)

    # ==========================================================
    # 2. PROCESAR EQUIPOS
    # ==========================================================
    update("Procesando equipos")
    df_equipos = df_jugadores_stats[["teamId", "teamName"]].drop_duplicates()

    id_equipos = df_equipos["teamId"].tolist()
    name_equipos = df_equipos["teamName"].tolist()
    slug_equipos = df_equipos["teamName"].str.replace(" ", "-", regex=True).tolist()

    equipos_dict = dict(zip(name_equipos, id_equipos))

    # ==========================================================
    # 3. CARGAR ESCUDOS
    # ==========================================================
    df_escudos = read_file(f"{SCRAPPING_FOLDER}escudos_equipo.xlsx")

    df_escudos.columns = df_escudos.columns.str.strip()
    names_equipo_escudo = df_escudos["Equipo"].tolist()
    logos_equipo_escudo = df_escudos["Logo"].tolist()

    # Normalizar mapa de escudos
    escudos_map_norm = {
        normalize_team_name(k): v
        for k, v in zip(names_equipo_escudo, logos_equipo_escudo)
    }

    # ==========================================================
    # 4. NORMALIZAR NOMBRES DE EQUIPOS PARA EMPAREJAR ESCUDOS
    # ==========================================================
    df_equipos["norm_name"] = df_equipos["teamName"].apply(normalize_team_name)

    df_equipos["escudo"] = df_equipos["norm_name"].map(escudos_map_norm)

    # Convertir a listas finales
    escudos = df_equipos["escudo"].tolist()

    # ==========================================================
    # 5. GENERAR EXCEL DE EQUIPOS (ID + NOMBRE + SLUG + ESCUDO)
    # ==========================================================
    equipos = init_excel_db(
        f"{INITTED_FOLDER}equipos_info_db.xlsx",
        ["id_equipo", "nombre", "slug", "escudo"],
        [id_equipos, name_equipos, slug_equipos, escudos],
        duplicates=["id_equipo"]
    )

    # ==========================================================
    # 6. ESTADIOS
    # ==========================================================
    update("Procesando estadios")

    df_estadios = df_partidos_info[
        ["Estadio", "Capacidad", "Latitud", "Longitud", "Local"]
    ].drop_duplicates()

    df_estadios["id_equipo"] = df_estadios["Local"].map(equipos_dict)

    df_estadios["id_estadio"] = df_estadios.apply(
        lambda r: make_stadium_id(
            r["Estadio"], r["Latitud"], r["Longitud"]
        ),
        axis=1
    )

    estadios = init_excel_db(
        f"{INITTED_FOLDER}estadios_info_db.xlsx",
        ["id_estadio", "nombre", "latitud", "longitud", "capacidad", "id_equipo"],
        [
            df_estadios["id_estadio"].tolist(),
            df_estadios["Estadio"].tolist(),
            df_estadios["Latitud"].tolist(),
            df_estadios["Longitud"].tolist(),
            df_estadios["Capacidad"].tolist(),
            df_estadios["id_equipo"].tolist()
        ],
        duplicates=["id_estadio"]
    )

    # ==========================================================
    # 7. PARTIDOS
    # ==========================================================
    update("Procesando partidos")

    df_partidos_info = df_partidos_info.merge(
        df_estadios[["Estadio", "id_estadio"]],
        on="Estadio",
        how="left"
    )

    df_partidos_info["id_temporada"] = 1
    df_partidos_info["id_partido"]   = df_partidos_info["id"]
    df_partidos_info["id_jornada"]   = df_partidos_info["Jornada"]
    df_partidos_info["id_local"]     = df_partidos_info["Local"].map(equipos_dict)
    df_partidos_info["id_visitante"] = df_partidos_info["Visitante"].map(equipos_dict)
    # df_partidos_info["id_estadio"]   = df_partidos_info["id_local"] * 100

    df_partidos_info["inicio"] = pd.to_datetime(
        df_partidos_info["Fecha"].astype(str) + " " + df_partidos_info["Hora"].astype(str),
        format="%d/%m/%Y %H:%M"
    ).dt.strftime("%d/%m/%Y %H:%M:%S")

    df_partidos_info["goles_local"]     = df_partidos_info["Resultado"].map(lambda x: int(x.split("-")[0].strip()))
    df_partidos_info["goles_visitante"] = df_partidos_info["Resultado"].map(lambda x: int(x.split("-")[1].strip()))
    df_partidos_info["estado"]          = "TERMINADO"

    df_partidos_info = df_partidos_info[
        ["id_partido", "id_temporada", "id_jornada",
        "id_local", "id_visitante", "id_estadio",
        "inicio", "estado", "goles_local", "goles_visitante"]
    ]

    # ==========================================================
    # 8. GUARDAR PARTIDOS
    # ==========================================================
    obj_path_partidos_info = init_path_object(new_path_folder_partidos_info)
    path_partidos_info_for_db = f"{obj_path_partidos_info['folder']}{obj_path_partidos_info['filename']}_db.{obj_path_partidos_info['extension']}"

    df_partidos_info.to_excel(path_partidos_info_for_db, index=False)

    # ==========================================================
    # 9. JORNADAS
    # ==========================================================
    update("Generando jornadas")
    df_jorn = df_partidos_info[["id_jornada", "id_temporada"]].drop_duplicates()

    jornadas = init_excel_db(
        f"{INITTED_FOLDER}jornadas_info_db.xlsx",
        ["id_jornada", "id_temporada","fecha_creacion"],
        [df_jorn["id_jornada"].tolist(), df_jorn["id_temporada"].tolist(), [now_ts() for _ in df_jorn["id_jornada"].tolist()]]
    )

    # ==========================================================
    # 10. TEMPORADAS
    # ==========================================================
    update("Generando temporadas")
    df_partidos_info["year"] = df_partidos_info["inicio"].apply(lambda x: x.split(" ")[0].split("/")[-1])

    years          = df_partidos_info["year"].tolist()
    nombres_temp   = [f"LaLiga {y}" for y in years]
    years_start    = [y[2:] for y in years]
    years_end      = [str(int(y) + 1)[2:] for y in years]

    temporadas = init_excel_db(
        f"{INITTED_FOLDER}temporadas_info_db.xlsx",
        ["id_temporada", "nombre", "year_start", "year_end", "id_liga", "fecha_creacion"],
        [df_jorn["id_temporada"].tolist(), nombres_temp, years_start, years_end, [now_ts() for _ in nombres_temp], [now_ts() for _ in nombres_temp]]
    )

    # ==========================================================
    # 11. JUGADORES
    # ==========================================================
    update("Procesando jugadores")
    df_jugadores_stats["age"] = df_jugadores_stats["dateOfBirthTimestamp"].apply(edad_from_timestamp)

    df_jugadores_stats["id_jugador"] = df_jugadores_stats.apply(
        lambda row: make_player_id(row["name"], row["teamId"], row["dateOfBirthTimestamp"]),
        axis=1
    )

    df_jug = df_jugadores_stats[["id_jugador", "name", "age", "gender", "country_alpha3", "teamId","dateOfBirthTimestamp"]].drop_duplicates()

    df_jug["id_jugador_"] = df_jug["id_jugador"].astype(str) + df_jug["teamId"].astype(str) + df_jug["dateOfBirthTimestamp"].astype(str)

    jugadores = init_excel_db(
        f"{INITTED_FOLDER}jugadores_info_db.xlsx",
        ["id_jugador", "nombre", "edad", "sexo", "country_name", "id_equipo","fecha_nacimiento"],
        [
            df_jug["id_jugador_"].tolist(),
            df_jug["name"].tolist(),
            df_jug["age"].tolist(),
            df_jug["gender"].tolist(),
            df_jug["country_alpha3"].tolist(),
            df_jug["teamId"].tolist(),
            df_jug["dateOfBirthTimestamp"].tolist()
        ],
        duplicates=["nombre", "id_equipo"]
    )

    # ==========================================================
    # APARTADO DE ESTADISTICAS
    # ==========================================================
    # ==========================================================
    # 12. PROCESAR ESTADÍSTICAS FINALES
    # ==========================================================
    update("Procesando ficheros")
    df_stats = pd.read_excel(f"{INITTED_FOLDER}jugadores_stats.xlsx")
    df_info  = pd.read_excel(f"{INITTED_FOLDER}jugadores_info_db.xlsx")

    # Normalizar nombres para hacer merge
    df_stats["name_norm"]  = df_stats["name"].str.lower().str.strip()
    df_info["nombre_norm"] = df_info["nombre"].str.lower().str.strip()

    # ==========================================================
    # 2. MERGE PARA CONSEGUIR id_jugador
    # ==========================================================
    df_merged = df_stats.merge(
        df_info[["id_jugador", "nombre_norm", "id_equipo"]],
        left_on=["name_norm", "teamId"],
        right_on=["nombre_norm", "id_equipo"],
        how="inner"
    )

    # ==========================================================
    # 3. LISTA DE ESTADÍSTICAS IMPORTANTES
    # ==========================================================
    extra_stats = PLAYER_STATS_FIELDS

    # ==========================================================
    # 4. CONSTRUIR DATAFRAME FINAL
    # ==========================================================

    # ==========================================================
    # 5. CREAR ID AUTOINCREMENT
    # ==========================================================
    
    df_final = df_merged.copy()

    df_final.insert(0, "id_estadistica_jugadores", range(1, len(df_final) + 1))

    df_final["id_equipo"] = df_final["teamId"] 
    df_final["id_partido"] = df_final["Partido"] 
    df_final["id_jornada"] = df_final["Jornada"] 

    essential_cols = [
        "id_estadistica_jugadores",
        "id_jugador",
        "id_equipo",
        "id_partido",
        "id_jornada"
    ]

    extra_stats = PLAYER_STATS_FIELDS

    all_cols = essential_cols + extra_stats
    df_final = df_final[all_cols]

    df_final = df_final.reset_index(drop=True)

    df_final = df_final.where(pd.notnull(df_final), 0)

    output_path = f"{INITTED_FOLDER}jugadores_stats_info_db.xlsx"

    export(output_path, df_final)

    # UNA VEZ QUEYA HAY RELACON ENTRE STATS JUGADORES E INFO JUGADORES PODEMOS ASIGNARLE MAS DATOS A LOS JUGADORES COMO: POSICION,ALTURA, ETC
    df_stats = pd.DataFrame(pd.read_excel(f"{INITTED_FOLDER}jugadores_stats_info_db.xlsx"))

    df_info = pd.DataFrame(pd.read_excel(f"{INITTED_FOLDER}jugadores_info_db.xlsx"))

    df_ = df_stats[["id_jugador", "position"]].drop_duplicates()

    df_info = df_info.merge(df_, on="id_jugador", how="left")

    export(f"{INITTED_FOLDER}jugadores_info_db.xlsx", df_info)

    # separar posiciones a otro excel
    df_positions = df_stats[["position"]].drop_duplicates()

    df_positions.insert(0,"id_posicion",range(1, len(df_positions) + 1))

    df_positions["posicion"] = df_positions["position"]

    df_positions = df_positions[["id_posicion","posicion"]]

    export( f"{INITTED_FOLDER}posiciones_info_db.xlsx" , df_positions )

    ids_posiciones = list( np.array( df_positions["id_posicion"] ) )

    names_posiciones = list( np.array( df_positions["posicion"] ) )

    posiciones = dict( zip( names_posiciones, ids_posiciones ) )

    df_info["id_posicion"] = df_info["position"].map(posiciones)

    df_info = df_info[["id_jugador","nombre","edad","sexo","country_name","id_posicion","id_equipo"]]

    export(f"{INITTED_FOLDER}jugadores_info_db.xlsx", df_info)

    # FIN DEL PIPELINE
    update("Completado")

if __name__ == "__main__":

    run_init_files()
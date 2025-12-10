from helpers.sofa_utils import *
from params import *
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

def predecir_jornadas_futuras(model, df_partidos, df_equipos, n_jornadas=5):
    """
    Genera predicciones para las próximas N jornadas, simulando todo el calendario.
    """

    resultados_futuros = []
    df_simulado = df_partidos.copy()

    for j in range(n_jornadas):
        print(f"\n🔵 Generando jornada simulada {j+1}/{n_jornadas}...")

        # 1. generar emparejamientos
        equipos = df_equipos[["id_equipo", "nombre"]].sample(frac=1).reset_index(drop=True)

        matches = []
        for i in range(0, len(equipos), 2):
            if i + 1 < len(equipos):
                local = equipos.iloc[i]
                visit = equipos.iloc[i+1]
                matches.append({
                    "id_local": local["id_equipo"],
                    "id_visitante": visit["id_equipo"],
                    "local": local["nombre"],
                    "visitante": visit["nombre"]
                })

        df_next = pd.DataFrame(matches)

        # 2. generar features como si fueran datos reales
        df_last = df_simulado.sort_values("inicio").groupby("id_local").tail(1)

        def get_last(team_id, col):
            row = df_last[df_last["id_local"] == team_id]
            if len(row) == 0:
                return 0
            return row[col].values[0]

        # features que necesita el modelo
        features = [
            "gf_local_prev","gc_local_prev",
            "gf_visit_prev","gc_visit_prev",
            "form_local","form_visit",
            "rating_local","rating_visit"
        ]

        # rellenar datos simulados
        df_next["gf_local_prev"] = df_next["id_local"].apply(lambda x: get_last(x, "goles_local"))
        df_next["gc_local_prev"] = df_next["id_local"].apply(lambda x: get_last(x, "goles_visitante"))

        df_next["gf_visit_prev"] = df_next["id_visitante"].apply(lambda x: get_last(x, "goles_visitante"))
        df_next["gc_visit_prev"] = df_next["id_visitante"].apply(lambda x: get_last(x, "goles_local"))

        df_next["form_local"] = df_next["id_local"].apply(lambda x: get_last(x, "form_local"))
        df_next["form_visit"] = df_next["id_visitante"].apply(lambda x: get_last(x, "form_visit"))

        df_next["rating_local"] = df_next["id_local"].apply(lambda x: get_last(x, "rating_local"))
        df_next["rating_visit"] = df_next["id_visitante"].apply(lambda x: get_last(x, "rating_visit"))

        # 3. predicción
        pred = model.predict(df_next[features])
        proba = model.predict_proba(df_next[features])

        mapping = {1:"Gana Local",2:"Gana Visitante",0:"Empate"}

        df_next["prediccion"] = pred
        df_next["prediccion"] = df_next["prediccion"].map(mapping)

        df_next["prob_local"] = proba[:,1]
        df_next["prob_visit"] = proba[:,2]
        df_next["prob_empate"] = proba[:,0]

        resultados_futuros.append(df_next)

        # 4. AÑADIR RESULTADOS SIMULADOS A LA TEMPORADA (para que afecten la siguiente jornada)
        df_tmp = df_next.copy()
        df_tmp["goles_local"] = (df_tmp["prob_local"] * 3).round().astype(int)
        df_tmp["goles_visitante"] = (df_tmp["prob_visit"] * 3).round().astype(int)
        df_tmp["inicio"] = pd.Timestamp.now()

        df_simulado = pd.concat([df_simulado, df_tmp], ignore_index=True)

    return resultados_futuros


# ================================
# 1) CARGA DE ARCHIVOS
# ================================
df_partidos = read_file(f"{INITTED_FOLDER}partidos_info_db.xlsx")
df_equipos = read_file(f"{INITTED_FOLDER}equipos_info_db.xlsx")
df_stats = read_file(f"{INITTED_FOLDER}jugadores_stats_info_db.xlsx")

# Parseo correcto de fechas
df_partidos["inicio"] = pd.to_datetime(
    df_partidos["inicio"],
    format="%d/%m/%Y %H:%M:%S",
    errors="coerce"
)

# ================================
# 2) FEATURE ENGINEERING
# ================================

# Goles totales previos local
df_partidos["gf_local_prev"] = df_partidos.groupby("id_local")["goles_local"].shift(1)
df_partidos["gc_local_prev"] = df_partidos.groupby("id_local")["goles_visitante"].shift(1)

# Goles totales previos visitante
df_partidos["gf_visit_prev"] = df_partidos.groupby("id_visitante")["goles_visitante"].shift(1)
df_partidos["gc_visit_prev"] = df_partidos.groupby("id_visitante")["goles_local"].shift(1)

# Racha últimos 5 partidos
def compute_form(df, team_col, gf_col, gc_col):
    df_team = df[[team_col, gf_col, gc_col]].copy()
    df_team["points"] = np.where(df_team[gf_col] > df_team[gc_col], 3,
                          np.where(df_team[gf_col] == df_team[gc_col], 1, 0))
    df_team["form5"] = df_team.groupby(team_col)["points"].rolling(5).sum().reset_index(level=0, drop=True)
    return df_team["form5"]

df_partidos["form_local"] = compute_form(df_partidos, "id_local", "goles_local", "goles_visitante")
df_partidos["form_visit"] = compute_form(df_partidos, "id_visitante", "goles_visitante", "goles_local")

# Rating medio por equipo
df_stats_group = df_stats.groupby(["id_partido", "id_equipo"])["rating"].mean().reset_index()
df_stats_group.columns = ["id_partido", "id_equipo", "rating_mean"]

df_partidos = df_partidos.merge(
    df_stats_group,
    left_on=["id_partido", "id_local"],
    right_on=["id_partido", "id_equipo"],
    how="left"
).rename(columns={"rating_mean": "rating_local"}).drop(columns=["id_equipo"])

df_partidos = df_partidos.merge(
    df_stats_group,
    left_on=["id_partido", "id_visitante"],
    right_on=["id_partido", "id_equipo"],
    how="left"
).rename(columns={"rating_mean": "rating_visit"}).drop(columns=["id_equipo"])

# Variable objetivo
df_partidos["resultado"] = np.where(df_partidos["goles_local"] > df_partidos["goles_visitante"], 1,
                             np.where(df_partidos["goles_local"] < df_partidos["goles_visitante"], 2, 0))

# ================================
# 3) ENTRENAMIENTO DEL MODELO
# ================================

# Requerimos solo que haya goles previos
df_model = df_partidos.dropna(subset=[
    "gf_local_prev","gf_visit_prev"
]).copy()

# Rellenamos el resto para evitar dataset vacío
df_model["gc_local_prev"] = df_model["gc_local_prev"].fillna(0)
df_model["gc_visit_prev"] = df_model["gc_visit_prev"].fillna(0)
df_model["form_local"] = df_model["form_local"].fillna(0)
df_model["form_visit"] = df_model["form_visit"].fillna(0)

# Ratings: si falta, ponemos la media (estrategia estándar)
df_model["rating_local"] = df_model["rating_local"].fillna(df_model["rating_local"].mean())
df_model["rating_visit"] = df_model["rating_visit"].fillna(df_model["rating_visit"].mean())

features = [
    "gf_local_prev","gc_local_prev","gf_visit_prev","gc_visit_prev",
    "form_local","form_visit","rating_local","rating_visit"
]

X = df_model[features] # dependence variables
y = df_model["resultado"] # independence variable

# Si aun así hay menos de 5 partidos, evitamos train_test_split
if len(df_model) < 5:
    print("⚠️ Muy pocos partidos para entrenar. Entrenando con todo el dataset...")
    model = RandomForestClassifier(n_estimators=300)
    model.fit(X, y)
else:
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, shuffle=True
    )

    model = RandomForestClassifier(n_estimators=300)
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    print("🔮 Accuracy del modelo:", accuracy_score(y_test, pred))

# ================================
# 4) GENERAR SIGUIENTE JORNADA AUTOMÁTICAMENTE
# ================================
print("⚽ Generando jornada simulada...")

equipos = df_equipos[["id_equipo", "nombre"]].sample(frac=1, random_state=42).reset_index(drop=True)

# Emparejamientos automáticos tipo liga
matches = []
for i in range(0, len(equipos), 2):
    if i + 1 < len(equipos):
        local = equipos.iloc[i]
        visit = equipos.iloc[i+1]
        matches.append({
            "id_local": local["id_equipo"],
            "id_visitante": visit["id_equipo"],
            "local": local["nombre"],
            "visitante": visit["nombre"]
        })

df_next = pd.DataFrame(matches)

# Unimos features previas desde df_partidos
df_last = df_partidos.sort_values("inicio").groupby("id_local").tail(1)

def get_last_values(team_id, col):
    row = df_last[df_last["id_local"] == team_id]
    if len(row) == 0:
        return 0
    return row[col].values[0]

for col in ["gf_local_prev","gc_local_prev","form_local","rating_local"]:
    df_next[col] = df_next["id_local"].apply(lambda x: get_last_values(x, col))

for col in ["gf_visit_prev","gc_visit_prev","form_visit","rating_visit"]:
    df_next[col] = df_next["id_visitante"].apply(lambda x: get_last_values(x, col.replace("visit","local")))

# ================================
# 5) PREDICCIÓN FINAL
# ================================
X_pred = df_next[features]
pred = model.predict(X_pred)
proba = model.predict_proba(X_pred)

mapping = {1: "Gana Local", 2: "Gana Visitante", 0: "Empate"}

df_next["predicción"] = pred
df_next["predicción"] = df_next["predicción"].map(mapping)

df_next["prob_local"] = proba[:,1]
df_next["prob_visit"] = proba[:,2]
df_next["prob_empate"] = proba[:,0]

# print("\n📌 Predicciones de la jornada simulada:\n")
# print(df_next[[
#     "local","visitante","predicción",
#     "prob_local","prob_visit","prob_empate"
# ]])

if __name__ == "__main__":

    res = predecir_jornadas_futuras(model, df_partidos, df_equipos, n_jornadas=2)

    print( res )
from helpers.sofa_utils import *
from params import *

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import math
from typing import Union
import re
import unicodedata
from typing import Union 


# ==========================================================
# UTILIDADES
# ==========================================================

def clean_dict(obj):
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return 0
    if isinstance(obj, dict):
        return {k: clean_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_dict(v) for v in obj]
    return obj


# ==========================================================
# SLUGS Y MATCHING ROBUSTO
# ==========================================================
def normalize_slug(slug: Union[str, None]) -> str:
    """
    Normalización estricta para matching interno
    """
    if not slug:
        return ""

    slug = slug.lower()

    # quitar tildes
    slug = unicodedata.normalize("NFD", slug)
    slug = slug.encode("ascii", "ignore").decode("utf-8")

    # mantener letras, numeros y guiones
    slug = re.sub(r"[^a-z0-9\-]", "", slug)

    return slug.strip()


def extract_match_slug(url: str) -> str:
    try:
        return url.split("/match/")[1].split("/")[0].lower()
    except Exception:
        return ""


def prepare_equipos_df(df_equipos: pd.DataFrame) -> pd.DataFrame:
    df = df_equipos.copy()
    df["slug_norm"] = (
        df["slug"]
        .astype(str)
        .str.lower()
        .str.strip()
    )
    return df


def build_alias_to_id_map(df_equipos: pd.DataFrame) -> dict:
    """
    alias_slug -> id_equipo
    """
    alias_map = {}

    for _, row in df_equipos.iterrows():
        slug = normalize_slug(row["slug_norm"])
        id_ = int(row["id_equipo"])

        alias_map[slug] = id_

        # Alias habituales de SofaScore
        if slug == "alaves":
            alias_map["deportivo-alaves"] = id_
        if slug == "athletic":
            alias_map["athletic-club"] = id_
        if slug == "atletico":
            alias_map["atletico-madrid"] = id_
        if slug == "girona":
            alias_map["girona-fc"] = id_
        if slug == "levante":
            alias_map["levante-ud"] = id_
        if slug == "betis":
            alias_map["real-betis"] = id_

    return alias_map


def extract_local_visit_slugs(match_slug: str):
    """
    Genera combinaciones ordenadas local/visitante
    respetando el orden del slug
    """
    parts = match_slug.split("-")
    for i in range(1, len(parts)):
        yield "-".join(parts[:i]), "-".join(parts[i:])


def find_team_ids_from_match_slug(match_slug: str, alias_map: dict):
    """
    Devuelve (id_local, id_visitante) o (None, None)
    """
    
    for local_slug, visit_slug in extract_local_visit_slugs(match_slug):
        if local_slug in alias_map and visit_slug in alias_map:
            return alias_map[local_slug], alias_map[visit_slug] , local_slug , visit_slug

    print(f"⚠️ Equipos no detectados en slug: {match_slug} {alias_map}")
    return None, None, None, None


# ==========================================================
# FEATURES
# ==========================================================

def build_features_from_history(id_local, id_visit, df_partidos):

    df_last = df_partidos.sort_values("inicio").groupby("id_local").tail(1)

    def get_last(team_id, col):
        row = df_last[df_last["id_local"] == team_id]
        if row.empty:
            return 0
        val = row[col].values[0]
        return 0 if pd.isna(val) else val

    return {
        "gf_local_prev": get_last(id_local, "gf_local_prev"),
        "gc_local_prev": get_last(id_local, "gc_local_prev"),
        "gf_visit_prev": get_last(id_visit, "gf_visit_prev"),
        "gc_visit_prev": get_last(id_visit, "gc_visit_prev"),
        "form_local": get_last(id_local, "form_local"),
        "form_visit": get_last(id_visit, "form_visit"),
        "rating_local": get_last(id_local, "rating_local"),
        "rating_visit": get_last(id_visit, "rating_visit"),
    }


# ==========================================================
# MODELO PRINCIPAL
# ==========================================================

def predict():

    # ======================================
    # 1) CARGA DE DATOS
    # ======================================
    df_partidos = read_file(f"{INITTED_FOLDER}partidos_info_db.xlsx")
    df_equipos = read_file(f"{INITTED_FOLDER}equipos_info_db.xlsx")
    df_stats = read_file(f"{INITTED_FOLDER}jugadores_stats_info_db.xlsx")

    df_partidos["inicio"] = pd.to_datetime(
        df_partidos["inicio"],
        format="%d/%m/%Y %H:%M:%S",
        errors="coerce"
    )

    df_equipos = prepare_equipos_df(df_equipos)
    alias_map = build_alias_to_id_map(df_equipos)

    # ======================================
    # 2) FEATURE ENGINEERING
    # ======================================
    df_partidos["gf_local_prev"] = df_partidos.groupby("id_local")["goles_local"].shift(1)
    df_partidos["gc_local_prev"] = df_partidos.groupby("id_local")["goles_visitante"].shift(1)

    df_partidos["gf_visit_prev"] = df_partidos.groupby("id_visitante")["goles_visitante"].shift(1)
    df_partidos["gc_visit_prev"] = df_partidos.groupby("id_visitante")["goles_local"].shift(1)

    def compute_form(df, team_col, gf_col, gc_col):
        df_team = df[[team_col, gf_col, gc_col]].copy()
        df_team["points"] = np.where(
            df_team[gf_col] > df_team[gc_col], 3,
            np.where(df_team[gf_col] == df_team[gc_col], 1, 0)
        )
        return (
            df_team.groupby(team_col)["points"]
            .rolling(5)
            .sum()
            .reset_index(level=0, drop=True)
        )

    df_partidos["form_local"] = compute_form(
        df_partidos, "id_local", "goles_local", "goles_visitante"
    )
    df_partidos["form_visit"] = compute_form(
        df_partidos, "id_visitante", "goles_visitante", "goles_local"
    )

    df_stats_group = (
        df_stats.groupby(["id_partido", "id_equipo"])["rating"]
        .mean()
        .reset_index()
        .rename(columns={"rating": "rating_mean"})
    )

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

    df_partidos["resultado"] = np.where(
        df_partidos["goles_local"] > df_partidos["goles_visitante"], 1,
        np.where(df_partidos["goles_local"] < df_partidos["goles_visitante"], 2, 0)
    )

    df_model = df_partidos.dropna(
        subset=["gf_local_prev", "gf_visit_prev"]
    ).copy()

    df_model.fillna(0, inplace=True)

    features = [
        "gf_local_prev", "gc_local_prev",
        "gf_visit_prev", "gc_visit_prev",
        "form_local", "form_visit",
        "rating_local", "rating_visit"
    ]

    X = df_model[features]
    y = df_model["resultado"]

    model = RandomForestClassifier(n_estimators=300, random_state=42)

    if len(df_model) > 5:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, shuffle=True
        )
        model.fit(X_train, y_train)
        print("🔮 Accuracy:", accuracy_score(y_test, model.predict(X_test)))
    else:
        model.fit(X, y)

    # ======================================
    # 3) SIMULACIÓN DE JORNADAS FUTURAS
    # ======================================
    df_urls = pd.read_csv(f"{SCRAPPING_FOLDER}partidos_laliga.csv")

    ultima_jornada_jugada = df_partidos["id_jornada"].max()
    df_futuras = df_urls[df_urls["Jornada"] > ultima_jornada_jugada]

    resultados = {}

    for jornada in sorted(df_futuras["Jornada"].unique()):
        df_jornada = df_futuras[df_futuras["Jornada"] == jornada]
        pred_rows = []

        for _, row in df_jornada.iterrows():
            match_slug = extract_match_slug(row["URL"])

            id_local, id_visit , local, visit = find_team_ids_from_match_slug(
                match_slug,
                alias_map
            )

            if id_local is None:
                continue

            features_row = build_features_from_history(
                id_local, id_visit, df_partidos
            )

            print( id_local )

            pred_rows.append({
                "id_local": id_local,
                "id_visitante": id_visit,
                "local": normalize_slug(local).capitalize().replace("-", " "),
                "visitante": normalize_slug(visit).capitalize().replace("-", " "),
                **features_row
            })

        if not pred_rows:
            continue

        df_pred = pd.DataFrame(pred_rows)

        pred = model.predict(df_pred[features])
        proba = model.predict_proba(df_pred[features])

        mapping = {1: "Gana Local", 2: "Gana Visitante", 0: "Empate"}

        df_pred["prediccion"] = [mapping[p] for p in pred]
        df_pred["prob_local"] = proba[:, 1]
        df_pred["prob_visit"] = proba[:, 2]
        df_pred["prob_empate"] = proba[:, 0]

        resultados[f"Jornada_{int(jornada)}"] = df_pred.to_dict(orient="records")

    return {
        "simulaciones_futuras": clean_dict(resultados)
    }


# ==========================================================
# EJECUCIÓN LOCAL
# ==========================================================
if __name__ == "__main__":
    res = predict()
    print(res)
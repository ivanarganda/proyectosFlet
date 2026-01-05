import os
import sys
import polars as pl
import requests
from typing import Union, List, Tuple, Optional, Iterable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import csv
import hashlib
import random
import time
from params import LOCATIONIQ_API_KEY
import ast
import json
import glob
from pathlib import Path

max_workers = min(20, (os.cpu_count() or 4) * 4)

def delete_files( files: list ) -> bool:

    try:

        for file in files:

            os.remove(file)

        return True

    except Exception as e:

        print(e)

        return False

def is_autoincrement(series, tolerance=0.98):
    s = series.dropna()

    if len(s) < 3:
        return False

    # intentar convertir a entero
    try:
        s = pd.to_numeric(s, errors="raise").astype(int)
    except Exception:
        return False

    # deben ser únicos
    if s.nunique() != len(s):
        return False

    # comprobar incremento constante
    s_sorted = s.sort_values()
    diffs = s_sorted.diff().dropna()

    step = diffs.mode()
    if step.empty:
        return False

    return (diffs == step.iloc[0]).mean() >= tolerance

def detect_autoincrement_columns(df):
    return [
        col for col, series in df.items()
        if is_autoincrement(series)
    ]


def detect_id_columns(df):
    
    return [
        c for c in df.columns
        if c.lower().startswith("id") or c.lower().endswith("_id")
    ]

from itertools import combinations

def candidate_keys(columns, max_size=3):
    keys = []
    for r in range(1, min(len(columns), max_size) + 1):
        keys.extend(combinations(columns, r))
    return keys

def duplication_ratio(df, subset):
    total = len(df)
    unique = df.drop_duplicates(subset=list(subset))
    return 1 - (len(unique) / total)

def choose_best_key(df, candidates, threshold=(0.01, 0.5)):
    best = None
    best_ratio = 0

    for key in candidates:
        ratio = duplication_ratio(df, key)

        if threshold[0] < ratio < threshold[1]:
            if ratio > best_ratio:
                best_ratio = ratio
                best = key

    return best, best_ratio

def smart_dedup(df):

    # 1️⃣ AUTOINCREMENT PRIMERO (prioridad máxima)
    auto_ids = detect_autoincrement_columns(df)

    if auto_ids:
        key = (auto_ids[0],)
        return df.drop_duplicates(subset=list(key)), key,1

    # 2️⃣ IDS POR NAMING
    id_cols = detect_id_columns(df)

    if len(id_cols) == 0:
        return df, None,1

    # 3️⃣ columnas extra SOLO si existen
    extra_cols = [c for c in ["Partido", "Jornada"] if c in df.columns]

    all_cols = id_cols + extra_cols

    if len(all_cols) == 0:
        return df, None,1

    # 4️⃣ combinaciones
    keys = candidate_keys(all_cols)

    # 5️⃣ mejor clave por duplicación
    best_key, ratio = choose_best_key(df, keys)

    if best_key:
        return df.drop_duplicates(subset=list(best_key)), best_key

    return df, keys, len(keys)

def get_files(
    folder: str,
    pattern: Union[str, Iterable[str]],
    extensions: Union[None, str, Iterable[str]] = None
) -> list[str]:

    patterns = [pattern] if isinstance(pattern, str) else list(pattern)

    if extensions is None:
        extensions = ["*"]
    elif isinstance(extensions, str):
        extensions = [extensions]

    files = set()

    for p in patterns:
        for ext in extensions:
            files.update(
                glob.glob(f"{folder}*{p}*.{ext}")
            )

    return sorted(files)

def map_positions( position ):

    return {
        "D": "Defensa",
        "F": "Delantero",
        "G": "Portero",
        "M": "Medio centro"
    }.get( position , "Unknown" )


def color_from_name(name: str) -> str:
    h = hashlib.md5(name.encode("utf-8")).hexdigest()
    return f"#{h[:6]}"

def extract_market_value(x):
    if pd.isna(x):
        return None

    # Caso 1: dict real
    if isinstance(x, dict):
        return x.get("value")

    # Caso 2: string
    if isinstance(x, str):
        try:
            # intenta JSON válido
            return json.loads(x).get("value")
        except json.JSONDecodeError:
            try:
                # intenta dict estilo Python
                return ast.literal_eval(x).get("value")
            except (ValueError, SyntaxError):
                return None

    return None

def _export_handlers(df, path):
    return {
        "csv":  lambda: df.to_csv(path, index=False),
        "json": lambda: df.to_json(path, orient="records"),
        "xlsx": lambda: df.to_excel(path, index=False),
        "xls":  lambda: df.to_excel(path, index=False)
    }


def now_ts():
    return int(datetime.now().timestamp())

def normalize_team_name(name):
    if isinstance(name, str):
        return (
            name.lower()
                .replace("cf", "")
                .replace("c.f.", "")
                .replace("club de fútbol", "")
                .replace("fútbol club", "")
                .replace("ud", "")
                .replace("s.a.d.", "")
                .strip()
        )
    return name

import requests
import time

def get_place(lat, lon):
    try:
        url = (
            f"https://eu1.locationiq.com/v1/reverse"
            f"?key={LOCATIONIQ_API_KEY}&lat={lat}012&lon={lon}012&format=json&zoom=10"
        )

        r = requests.get(url, timeout=10)
        data = r.json()

        if "display_name" in data:
            return data["display_name"]

        address = data.get("address", {})
        return (
            address.get("city")
            or address.get("state")
            or address.get("country")
            or "Desconocido"
        )

    except Exception:
        return "Desconocido"


def make_stadium_id(nombre: str, lat: float, lon: float) -> int:
    base = f"{nombre}_{lat}_{lon}".lower().strip()
    return int(hashlib.md5(base.encode()).hexdigest()[:12], 16)

def make_player_id(name, teamId, dateBirth):

    raw = f"{name}-{teamId}-{dateBirth}".lower().strip()
    h = hashlib.md5(raw.encode()).hexdigest()
    return int(h[:14], 16)   # entero grande pero manejable

def edad_from_timestamp(ts):

    fecha_nac = datetime.utcfromtimestamp(int(ts)).date()
    hoy = datetime.now().date()
    edad = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
    return edad

def generate_json(**args):

    try:

        files = args.get("files", [])
        alias = args.get("alias", "")
        on_callback = args.get("on_callback", lambda x: None)
        folder = args.get("folder", "output")
        cleanup = args.get("cleanup", True)
        combine = args.get("combine", {})

        folder_path = Path(folder)
        folder_path.mkdir(parents=True, exist_ok=True)

        files_outputted = []

        for file in files:
            df = read_file(file)
            name = Path(file).stem

            report = on_callback(df)

            report_file = folder_path / f"{alias}{name}.json"

            if report is not None and not isinstance(report, dict):
                raise TypeError("callback must return dict or None")
            if report is not None:
                df_report = pd.DataFrame([report])
            else:
                df_report = df

            df_report.to_json(
                report_file,
                orient="records",
                force_ascii=False,
                indent=2
            )

            files_outputted.append(report_file)

        # 🔹 combinar si se solicita
        if not combine or "file" not in combine:
            return {
                "success": False,
                "files_processed": len(files_outputted),
                "combined": False
            }

        combined = {}

        for file in files_outputted:
            if file.exists():
                with open(file, "r", encoding="utf-8") as f:
                    combined[file.stem] = json.load(f)

        combined_path = folder_path / f"{combine['file']}.json"

        with open(combined_path, "w", encoding="utf-8") as f:
            json.dump(combined, f, ensure_ascii=False, indent=2)

        if cleanup:
            for file in files_outputted:
                file.unlink(missing_ok=True)

        return {
            "success": True,
            "files_processed": len(files_outputted),
            "combined": bool(combine)
        }

    except Exception as e:
        print(f"[generate_json] Error: {e}")
        return {
            "success": False,
            "files_processed": 0,
            "combined": False
        }

def combine_sheets_with_one(
    current_path: str,
    alias: str = "",
    new_file: Union[str, None] = None
) -> Union[str, bool]:

    from pathlib import Path

    xls = pd.ExcelFile(current_path)

    try:
        
        obj_path = init_path_object(current_path)

        Path("files_initted").mkdir(parents=True, exist_ok=True)

        if new_file is None:
            new_path = f"files_initted/{obj_path['filename']}{alias}.{obj_path['extension']}"
        else:
            new_path = f"files_initted/{new_file}.{obj_path['extension']}"

        print(f"Combining ALL sheets from {current_path} into {new_path}")

        all_dfs = []

        # ------------------------------------
        # Leer todas las hojas
        # ------------------------------------
        for sheet_name in xls.sheet_names:
            print(f"Processing {sheet_name}")
            df = pd.read_excel(xls, sheet_name=sheet_name)

            if df is None or df.empty:
                print(f"⚠️ Hoja {sheet_name} vacía → ignorada")
                continue

            # (opcional) añadir nombre de hoja como contexto
            df["__sheet"] = sheet_name

            all_dfs.append(df)

        # ------------------------------------
        # Validación final
        # ------------------------------------
        if not all_dfs:
            print("❌ No hay datos válidos en ninguna hoja")
            return False

        # ------------------------------------
        # CONCAT VERTICAL (CLAVE)
        # ------------------------------------
        df_final = pd.concat(all_dfs, ignore_index=True)
        df_final = df_final.loc[:, ~df_final.columns.duplicated()]

        # ------------------------------------
        # Escritura (sobrescribe siempre)
        # ------------------------------------
        df_final.to_excel(new_path, index=False)

        print(f"✅ Archivo generado correctamente: {new_path}")
        print(f"📊 Filas totales: {len(df_final)}")

        return new_path
    
    except Exception as e:
        print(f"❌ Error combinando hojas: {e}")
        return False
    
    finally:

        xls.close()


def init_path_object( path ):

    file = path.split("/")[-1]

    extension = file.split(".")[-1]

    filename = file.replace( f".{extension}" , "" )

    folder = path.replace( file , "" )

    return {

        "folder": folder,

        "extension": extension,

        "file": file,

        "filename": filename

    }

def replace_comas_by_dots(col):

    return col.astype(str).apply(lambda x: x.replace(",","."))

def _read(file):

    extensions = {
        "csv": {  "open": pl.read_csv, "encoding": "latin1"  },
        "json": { "open": pl.read_json, "encoding": "utf8-lossy"  },
        "xlsx": { "open": pl.read_excel, "encoding": "utf-8" },
        "xls": { "open": pl.read_excel, "encoding": "utf-8"  }
    }

    extension = file.split(".")[-1].lower()

    if extension not in extensions:

        raise ValueError(f"Unsupported file format: {extension}")
    
    file_ = extensions[extension]

    df = file_["open"](file)

    return df.to_pandas()

def read_file(file: str, workers=max_workers):

    with ThreadPoolExecutor(max_workers=workers) as executor:

        future = executor.submit(_read, file)

        try:

            return future.result()

        except Exception as e:

            raise RuntimeError(f"ERROR: {e}") from e

    return result

def export( path, data ):

    ext = path.split(".")[-1].lower()

    df = pd.DataFrame(data)

    handlers = _export_handlers(df, path)

    if ext not in handlers:
        raise ValueError(f"Unsupported export format: {ext}")

    handlers[ext]()  # ejecuta SOLO el formato elegido
    
def init_excel_db(new_file, keys, fields_values, duplicates=True):

    # Convert zip to list of dicts
    zipped = zip(*fields_values)
    output = [dict(zip(keys, row)) for row in zipped]

    # Procesar duplicados
    if duplicates:
        df = pd.DataFrame(output)

        # Si duplicates=True → eliminar duplicados por TODAS las keys
        if duplicates is True:
            df = df.drop_duplicates(subset=keys, keep="first")

        # Si duplicates=["col"] o ["col1","col2"]
        elif isinstance(duplicates, list):
            df = df.drop_duplicates(subset=duplicates, keep="first")

        output = df.to_dict(orient="records")

    # Exportar
    export(new_file, output)

    return output
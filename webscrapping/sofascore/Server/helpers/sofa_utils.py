import os
import sys
import polars as pl
import requests
from typing import Union, List, Tuple, Optional
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

max_workers = min(20, (os.cpu_count() or 4) * 4)


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

def combine_sheets_with_one(current_path: str, alias: str = "", new_file:Union[str,None] = None) -> Union[str, bool]:

    from pathlib import Path

    try:

        xls = pd.ExcelFile(current_path)

        obj_path = init_path_object(current_path)

        Path("files_initted").mkdir(parents=True, exist_ok=True)

        if new_file is None:
            
            new_path = f"files_initted/{obj_path.get('filename')}{alias}.{obj_path.get('extension')}"

        else:

            new_path = f"files_initted/{new_file}.{obj_path.get('extension')}"

        p = Path(new_path)

        if p.is_file():

            print(f"Este fichero {new_path} ya existe")

            return new_path
        
        def load_sheet(sheet_name):

            print(f"Processing {sheet_name} from {current_path}")

            return sheet_name, pd.read_excel(xls, sheet_name=sheet_name)

        sheet_names = xls.sheet_names

        sheet_data = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:

            futures = {executor.submit(load_sheet, sheet): sheet for sheet in sheet_names}

            for future in as_completed(futures):

                sheet_name, df = future.result()

                sheet_data[sheet_name] = df

        df_matchs_info = None

        for i in range(len(sheet_names) - 1):

            s1 = sheet_names[i]

            s2 = sheet_names[i + 1]

            if s1 == s2:

                continue

            df_current = sheet_data[s1]

            df_next = sheet_data[s2]

            if df_matchs_info is None:

                df_matchs_info = pd.merge(df_current, df_next, how='outer')

            else:

                df_matchs_info = pd.merge(df_matchs_info, df_next, how='outer')

        df_matchs_info.to_excel(new_path, index=False)

        return new_path

    except Exception as e:

        print(e)

        return False

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
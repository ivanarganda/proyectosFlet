import os
import sys
import polars as pl
from typing import Union, List, Tuple, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import csv
import hashlib
import random
import time

max_workers = min(20, (os.cpu_count() or 4) * 4)

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

    result = {}

    with ThreadPoolExecutor(max_workers=workers) as executor:

        futures = {executor.submit(_read, file)}

        for future in as_completed(futures):

            try:

                result = future.result()

            except Exception as e:

                result = f"ERROR: {e}"

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
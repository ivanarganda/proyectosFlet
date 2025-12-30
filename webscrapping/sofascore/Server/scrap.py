from pathlib import Path
import re
import pandas as pd
import polars as pl
import glob
import json
import os
import sys
import numpy as np
from ivbox.SQLiteORM import *
from typing import Union, Iterable
import time

from params import *
from helpers.sofa_utils import *

output_dir = Path("output")
pattern_innit_files = "_db"
pattern_scrapping_folder = ["jornadas", "estadisticas"]

db = SQLiteORM(DB)
db.connect_DB()

def run_scrapping(settings,progress_cb=None):

    def detect_id_columns(df):
        return [
            c for c in df.columns
            if c.lower() == "id" or c.lower().endswith("_id")
        ]

    from itertools import combinations

    def candidate_keys(columns, max_size=3):
        keys = []
        for r in range(1, min(len(columns), max_size) + 1):
            keys.extend(combinations(columns, r))
        return keys

    def duplication_ratio(df, subset):
        total = df.height
        unique = df.unique(subset=list(subset)).height
        return 1 - (unique / total)

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

        id_cols = detect_id_columns(df)
        if not id_cols:
            return df, None

        keys = candidate_keys(id_cols + ["Partido", "Jornada"])
        best_key, ratio = choose_best_key(df, keys)

        if best_key:
            return df.unique(subset=list(best_key)), best_key

        return df, None


    def save_as_sql():

        import sqlite3

        print("Saving as sql")

        files = get_files(INITTED_FOLDER, pattern_innit_files)

        output_dir.mkdir(exist_ok=True)

        conn = sqlite3.connect(output_dir / "info.db")

        try:
            for file in files:
                df = read_file(file)
                df, used_keys = smart_dedup(df)
                table_name = Path(file).stem
                df.to_sql(table_name, conn, if_exists="replace", index=False)
        finally:
            conn.close()


    def save_as_excel():

        print(f"Saving as excel")

        output_file = output_dir / "info.xlsx"

        excel_files = get_files( INITTED_FOLDER, pattern_innit_files )
        
        delimiters = []
        for file in excel_files:
            file = Path(file).stem
            delimiter = re.sub(f"^[^_]+","",file)
            delimiters.append(delimiter)

        if not excel_files:
            raise RuntimeError("No Excel files found")

        with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
            for key,file in enumerate(excel_files):
                df = read_file(file)
                df, used_keys = smart_dedup(df)
                stem = Path(file).stem
                sheet_name = re.sub(r"_[^_]+$", "", stem)  # límite Excel
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        print(f"✅ Excel combinado generado: {output_file}")

    def save_as_csv():
        def normalize_schema(dfs: list[pl.DataFrame]) -> list[pl.DataFrame]:

            all_columns = set()
            for df in dfs:
                all_columns.update(df.columns)

            all_columns = list(all_columns)

            normalized = []
            for df in dfs:
                missing = [c for c in all_columns if c not in df.columns]

                if missing:
                    df = df.with_columns([
                        pl.lit(None).alias(c) for c in missing
                    ])

                # mismo orden de columnas
                df = df.select(all_columns)
                normalized.append(df)

            return normalized

        print("Saving as csv")

        path = output_dir / "info.csv"
        files = get_files(INITTED_FOLDER, pattern_innit_files)

        dfs = []

        for file in files:
            df_pd = read_file(file)          # Pandas
            df_pl = pl.from_pandas(df_pd)    # Polars
            dfs.append(df_pl)

        dfs = normalize_schema(dfs)

        df_combined = pl.concat(dfs, how="vertical_relaxed")
        df_combined.write_csv(path, separator=";")

    def save_as_json():

        print(f"Saving as json")

        files = get_files(INITTED_FOLDER, pattern_innit_files)

        files_outputted = []

        for file in files:
            df = read_file(file)
            
            name = Path(file).stem
            df.to_json(
                output_dir / f"{name}.json",
                orient="records",
                force_ascii=False,
                indent=2
            )
            files_outputted.append( output_dir / f"{name}.json" )

        combined = {}

        for file in files_outputted:
            if not file.exists():
                continue
            with open( file , "r", encoding="utf-8") as f:
                combined[file.stem] = json.load(f)
        
        with open( output_dir / "info.json", "w", encoding="utf-8" ) as f:
            json.dump( combined, f, ensure_ascii=False, indent=2 )

        delete_files( files_outputted )

    def output_save( type ):

        dispatches = {

            "sql": save_as_sql,
            "excel": save_as_excel,
            "csv": save_as_csv,
            "json": save_as_json

        }

        func = dispatches.get(type)

        if not func:
            raise ValueError(f"Unsupported output type: {type}")

        func()

    def update(step, current=None, total=None):
        if progress_cb:
            progress_cb(step, current, total)

    def delete_files( files: list ) -> bool:

        try:

            for file in files:

                os.remove(file)

            return True

        except Exception as e:

            print(e)

            return False


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


    def delete_files_initted( folder: str, pattern: Union[list, str] = pattern_innit_files, extensions: list = None ) -> bool:

        try:

            # Cuando NO hay filtro por extensión
            files = get_files( folder, pattern, extensions )

            delete_files( files )

            return True

        except Exception as e:

            print(e)

            return False

    def delete_scrapping_files(folder: str, pattern: Union[list, str] = pattern_scrapping_folder, extensions: list = None):

        try:

            # Cuando NO hay filtro por extensión
            files = get_files( folder, pattern, extensions )

            delete_files( files )

            return True

        except Exception as e:

            print(e)

            return False


    def _to_sql_tuples(path, columns):

        df = read_file( path )

        df = df[columns]

        # Convertir cada fila en tupla
        tuples = [tuple(row) for row in df.to_numpy()]

        rows = [
            tuple(int(x) if isinstance(x, (np.int64, np.int32)) else x for x in row)
            for row in tuples
        ]

        return rows

    def scrap_data( tables: dict )-> bool:

        total_tables = len(tables)
        table_index = 0

        update("Iniciando scraping", 0, total_tables)

        for table in tables:

            table_index += 1
            
            update(f"Procesando tabla {table}", table_index, total_tables)

            # if table != "jornadas": continue
            folder = tables[table]["folder"]

            file = tables[table]["file"]
            
            columns = tables[table]["columns"]

            path = f"{folder}{file}"

            print( table )

            db.insert_many(

                table,

                _to_sql_tuples(path, columns)

            )
        
        update("Scraping finalizado", total_tables, total_tables)

        if progress_cb:
            progress_cb("Scraping finalizado ✅", total=len(tables), current=len(tables))
            
    def get_tables( folder: str, files: list , delimiter: str = "" ) -> dict:
        
        tables = {}

        for file in files:

            path = f"{folder}{file}"

            obj_path = init_path_object( path )
            
            tables[ obj_path.get("filename").replace(delimiter,"") ] = {

                "folder": obj_path.get("folder"),

                "file": obj_path.get("file"),

                "columns":read_file( path ).columns

            }
        
        return tables
            
    def list_files(

        folder=INITTED_FOLDER,

        pattern="_db",

        extensions=None,

        sort=True

    ):
        try:

            files = []

            # Cuando NO hay filtro por extensión
            if extensions is None:

                files = glob.glob(f"{folder}*{pattern}*.*")

            else:
                # Filtro por extensiones
                for ext in extensions:

                    files.extend(glob.glob(f"{folder}*{pattern}*.{ext}"))

            # Ordenar
            if sort:

                files.sort()

            files = [Path(f).name for f in files]
 
            return folder, files

        except Exception as e:

            print(e)

            return False

    folder , files = list_files()

    tables = get_tables( folder, files , delimiter = "_info_db" )

    scrap_data( tables )

    output_save( settings.get("output_save") )

    time.sleep(0.3)

    if settings.get("clear_previous_data") == "si":

        delete_scrapping_files( SCRAPPING_FOLDER )

        delete_files_initted( INITTED_FOLDER )

if __name__ == "__main__":

    # FOR TESTING PURPOUSES
    run_scrapping({
        "clear_previous_data": "si",
        "output_save": "json"
    })
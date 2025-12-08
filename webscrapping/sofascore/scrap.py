from pathlib import Path
import pandas as pd
import polars as pl
import glob
import json
import os
import sys
import numpy as np
from ivbox.SQLiteORM import *

from params import *
from helpers.sofa_utils import *
db = SQLiteORM(DB)
db.connect_DB()

def run_scrapping():

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

        for table in tables:

            # if table != "jornadas": continue
            folder = tables[table]["folder"]

            file = tables[table]["file"]
            
            columns = tables[table]["columns"]

            path = f"{folder}{file}"

            print( _to_sql_tuples(path, columns) )

            db.insert_many(

                table,

                _to_sql_tuples(path, columns)

            )
            
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

if __name__ == "__main__":

    run_scrapping()
import sqlite3 as sql
from typing import Union, List, Tuple, Optional
import numpy as np
import os

# Auxiliar classes
from QueryResults import QueryResults

class SQLiteORM:

    def __init__(self, db_path: str):

        self.db_path = os.path.join(os.path.dirname(__file__) , db_path) or db_path
        self.db_name = os.path.basename(db_path) or db_path
        self.conn = None
        self.cursor = None
        self.query = None

    def get_database(self) -> str:

        if "db" in self.db_path: 
            return self.db_path
        return self.db_name

    def close_connection(self) -> None:

        self.conn.close()

    def conect_DB(self)-> Union[sql.Connection, None]:

        try:
            self.conn = sql.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sql.Row
            self.cursor = self.conn.cursor()
            self.cursor.execute("PRAGMA journal_mode=WAL;")
            print("✅ Connection success to database:", self.db_name.split('.')[0:(self.db_name.count('.'))][0])
            return self.conn
        except sql.Error as e:
            print(f"❌ Database error: {e}")
            return None

    def get_sqlite_type(self, value):
        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return "INTEGER"
        if isinstance(value, int):
            return "INTEGER"
        if isinstance(value, float):
            return "REAL"
        if isinstance(value, str):
            return "TEXT"
        if isinstance(value, bytes):
            return "BLOB"

        # Tipos especiales
        import datetime, decimal, uuid, json

        if isinstance(value, (datetime.date, datetime.datetime)):
            return "TEXT"  # ISO format recommended

        if isinstance(value, decimal.Decimal):
            return "NUMERIC"

        if isinstance(value, uuid.UUID):
            return "TEXT"

        if isinstance(value, (list, dict)):
            return "TEXT"  # Save as JSON

        # Cualquier otro tipo: guardarlo como texto
        return "TEXT"

    def get_pk(self, table_name):

        import json

        primary_keys = [ { "name": field.get("name") , "type": field.get("type") } for field in self.get_object_columns( table_name ) if field.get("pk") == 1]

        return list( primary_keys )

    def get_query(self) -> str:
        
        return self.query

    def get_object_columns(self, table_name: str) -> Union[dict, None]:

        try:
            columns = self.execute_query(f"PRAGMA table_info({table_name});").json
            return columns
        except sql.Error as e:
            print(f"⚠️ Error fetching columns for {table_name}: {e}")
            return None

    def check_columns(self, table_name: str) -> Union[list, None]:

        try:
            self.cursor.execute(f"PRAGMA table_info({table_name});")
            columns_info = self.cursor.fetchall()
            columns = [col['name'] for col in columns_info]
            return columns
        except sql.Error as e:
            print(f"⚠️ Error fetching columns for {table_name}: {e}")
            return None

    def check_table(self, table_name):

        import json
        
        try:
        
            data = self.execute_query("""
                SELECT name FROM sqlite_master WHERE type='table' AND name = ?
            """, (table_name,)).count

            if data == 0:
                raise Exception(f"Not found table {table_name}")
            
            return True
    
        except Exception as e:
            print(f"Error: {e}")
            return False

    def execute_query(self, query: str, params: Union[tuple, list, None]=None) -> Union[list, bool]:

        import re

        try:

            # Check if all tables over query exist
            if params is None:
                result = self.cursor.execute(query)

            elif isinstance(params, list):
                
                if all(isinstance(p, (list, tuple)) for p in params):
                    result = self.cursor.executemany(query, params)
                else:
                    raise ValueError("Params must be a list of tuples or lists for executemany().")

            else:
                result = self.cursor.execute(query, params)

            self.conn.commit()

            cmd = query.lstrip().split()[0].upper()

            if cmd in ("SELECT", "PRAGMA", "WITH"):

                rows = result.fetchall()
                return QueryResults(rows, formatter=self.format_results)

            return True

        except sql.Error as e:
            print(f"⚠️ Query error: {e}")
            return False


    # ===============================
    # INSERT ORM ( insert both single values and many values)
    # ===============================
    def insert_many(self, size: int, table_name: str, pattern, chunk_size=50000):

        """
        Inserta 'size' registros en modo TURBO usando NumPy + streaming.
        - No guarda todos los datos en RAM
        - Genera bloques con NumPy ultra rápido
        - Usa PRAGMA turbo para máxima velocidad
        """

        try:
            print(f"INSERT NUMPY TURBO INIT ({size:,} rows)…")

            self.execute_query("PRAGMA synchronous = OFF;")
            self.execute_query("PRAGMA journal_mode = MEMORY;")
            self.execute_query("PRAGMA temp_store = MEMORY;")
            self.execute_query("PRAGMA locking_mode = EXCLUSIVE;")
            self.execute_query("PRAGMA foreign_keys = OFF;")
            self.execute_query("PRAGMA cache_size = -2000000;")

            example = pattern(0)
            num_cols = len(example)

            columns = self.check_columns(table_name)

            info = self.execute_query(f"PRAGMA table_info({table_name})")
            primary_keys = [col['name'] for col in info if col['pk'] == 1]
            
            placeholders = ", ".join(["?"] * ( len(columns) - len(primary_keys) ))
            base_query = (
                f"INSERT INTO {table_name} ({', '.join([col for col in columns if col not in primary_keys])}) "
                f"VALUES ({placeholders})"
            )

            print(f"✔ Using {num_cols} columns")
            print(f"✔ Chunk size: {chunk_size:,}")

            for start in range(0, size, chunk_size):

                end = min(start + chunk_size, size)
                block_len = end - start

                col0 = np.arange(start + 1, end + 1)

                # Generar las demás columnas (solo se repiten, no se recalculan)
                cols = [None] * num_cols
                cols[0] = col0

                for col_index in range(1, num_cols):
                    value = example[col_index]

                    if isinstance(value, str):
                        cols[col_index] = np.repeat(value, block_len)
                    else:
                        cols[col_index] = np.full(block_len, value, dtype=object)

                block = list(zip(*cols))

                self.execute_query(base_query, block)

                print(f"   → Inserted {end:,}/{size:,}")

            self.execute_query("PRAGMA foreign_keys = ON;")
            self.execute_query("PRAGMA journal_mode = WAL;")
            self.execute_query("PRAGMA synchronous = NORMAL;")

            print("✅ INSERT NUMPY TURBO DONE")
            return True

        except Exception as e:
            print("❌ insert_numpy_turbo error:", e)
            return False

    def insert(self, data: Union[tuple, list], table_name: str )-> bool:

        try:
            if isinstance(data, (list, tuple)) and not any(isinstance(row, (list, tuple)) for row in data):
                columns_name_db =  self.check_columns( table_name )
                columns_type_db = [
                    self.execute_query(f"SELECT typeof({col}) as type from {table_name} limit 1")[0]['type']
                    for col in columns_name_db
                ]
                if len(data) != len(columns_name_db):
                    raise ValueError("Data length does not match number of columns in the table.")

                # Detect primary keys because they might be autoincrement amd it is not necessary to provide a value
                info = self.execute_query(f"PRAGMA table_info({table_name})")
                primary_keys = [col['name'] for col in info if col['pk'] == 1]
                placeholders = ", ".join(["?"] * ( len(data) - len(primary_keys) ))
                
                # Build insert or ignore into query
                query = f"INSERT OR IGNORE INTO {table_name} ({', '.join([col for col in columns_name_db if col not in primary_keys])}) VALUES ({placeholders})"
                print(f"Query: {query}")

                print(f"Placeholders: {placeholders}")
                args = tuple(
                    val for i, val in enumerate(data) 
                    if columns_name_db[i] not in primary_keys
                )
                
                self.execute_query(query, args)
                print("✅ Insert successful")
                return True            
            else:
                raise ValueError("Data must be a tuple/list for single insert or list of tuples/lists for multiple inserts.")
                
        except sql.Error as e:
            print(f"⚠️ Insert error: {e}")
            return False

    # ===============================
    # SELECT ORM ( select both by clasical and criterial)
    # ===============================
    def select_all(self, table: str):

        query = f"SELECT * FROM {table}"
        return self.execute_query(query)

    def select_one(self, table: str, **conditions):

        if not conditions:
            raise ValueError("select_one requires at least one condition.")

        conditions_list = [f"{col} = ?" for col in conditions]
        where = " AND ".join(conditions_list)
        params = tuple(conditions.values())

        query = f"SELECT * FROM {table} WHERE {where} LIMIT 1"
        result = self.execute_query(query, params)
        return result[0] if result else None

    def select_where(self, table: str, **conditions):

        conditions_list = [f"{col} = ?" for col in conditions]
        where = " AND ".join(conditions_list)
        params = tuple(conditions.values())

        query = f"SELECT * FROM {table} WHERE {where}"
        return self.execute_query(query, params)

    def select_columns(self, table: str, columns: list):

        cols = ", ".join(columns)
        query = f"SELECT {cols} FROM {table}"
        return self.execute_query(query)

    def select_by_id(self, table: str, id_column: str, id_value):

        query = f"SELECT * FROM {table} WHERE {id_column} = ? LIMIT 1"
        result = self.execute_query(query, (id_value,))
        return result[0] if result else None

    def select_like(self, table: str, column: str, pattern: str):

        query = f"SELECT * FROM {table} WHERE {column} LIKE ?"
        return self.execute_query(query, (pattern,))

    def select_in(self, table: str, column: str, values: list):
        
        placeholders = ", ".join("?" for _ in values)
        query = f"SELECT * FROM {table} WHERE {column} IN ({placeholders})"
        return self.execute_query(query, values)


    def reset_autoincrement(self, table_name: str, delete_rows: bool=False) -> bool:

        """
        Reset AUTOINCREMENT counter for a table.
        If delete_rows=True, also clears all rows from the table.
        """
        try:
            if delete_rows:
                self.cursor.execute(f"DELETE FROM {table_name};")

            self.cursor.execute("DELETE FROM sqlite_sequence WHERE name=?;", (table_name,))
            self.conn.commit()
            print(f"✅ AUTOINCREMENT reset for table '{table_name}'")
            return True
        except sql.Error as e:
            print(f"⚠️ Error resetting autoincrement for {table_name}: {e}")
            return False

    # ========================
    # DELETE RECORDS
    # ========================
    def delete(self, data: Union[list, int] = None, table_name: str = "") -> bool:
        try:

            # Validate table
            if self.check_table(table_name) == 0:
                raise Exception(f"Table '{table_name}' does not exist")

            # Obtain primary key
            primary_keys = self.get_pk(table_name)

            if len(primary_keys) == 0:
                raise Exception("Table has no primary key — cannot perform delete by ID.")

            if len(primary_keys) > 1:
                raise Exception(
                    f"Table has multiple primary keys. Choose one: {', '.join(pk['name'] for pk in primary_keys)}"
                )

            name_primary_key = primary_keys[0]["name"]
            type_primary_key = primary_keys[0]["type"]

            # =============================
            # CASE: data as only ID
            # =============================
            if isinstance(data, int):
                placeholders = "?"
                where = f" WHERE {name_primary_key} IN ({placeholders})"
                params = (data,)

            # =============================
            # CASE: data as a list of IDs
            # =============================
            elif isinstance(data, list) and len(data) > 0:
                # Validar tipos
                wrong_ids = [item for item in data if self.get_sqlite_type(item) != type_primary_key]

                if wrong_ids:
                    raise Exception(
                        f"IDs {', '.join(map(str, wrong_ids))} do not match primary key type '{type_primary_key}' in table '{table_name}'"
                    )

                # Crear placeholders seguros
                placeholders = ", ".join(["?"] * len(data))
                where = f" WHERE {name_primary_key} IN ({placeholders})"
                params = tuple(data)

            else:
                raise Exception("You must provide an integer ID or a list of IDs for deletion.")

            query = f"DELETE FROM {table_name}{where}"
            print("Executing:", query)
            print("Params:", params)

            self.execute_query(query, params)
            return True

        except Exception as e:
            print(f"Error: {e}")
            return False


    # ========================
    # FETCHING DATA
    # ========================  
    def fetch_all(self) -> list[dict]:

        rows = self.cursor.fetchall()

        results = [dict(row) for row in rows]

        return results

    def fetch_one(self) -> Union[dict, None]:

        row = self.cursor.fetchone()

        if row:
            return dict(row)
        return None
    
    def fetch_many(self, size: int) -> list[dict]:

        rows = self.cursor.fetchmany(size)

        results = [dict(row) for row in rows]

        return results

    # =====================
    # FORMATING DATA
    # =====================
    def format_table(self, data: list) -> str:

        if not data:
            return "No data available."

        headers = [f"Col{i+1}" for i in range(len(data[0]))]

        table = " | ".join(headers) + "\n"
        table += "-" * len(table) + "\n"
        for row in data:
            formatted_values = [str(value) for value in row]
            table += " | ".join(formatted_values) + "\n"

        return table

    def formatted_query(self) -> str:

        return self.query.strip().replace("\n", " ").replace("  ", " ")
    
    def format_results(self, rows: list[dict]) -> str:

        if not rows:
            return "No results found."

        headers = rows[0].keys()

        table = " | ".join(headers) + "\n"
        table += "-" * len(table) + "\n"

        for row in rows:
            formatted_values = []
            for h in headers:
                value = row[h]

                if value is None and isinstance(value, str):
                    formatted = ""
                elif isinstance(value, (int, float)) and value is None:
                    formatted = str(value)
                else:
                    formatted = str(value)

                formatted_values.append(formatted)

            table += " | ".join(formatted_values) + "\n"

        return table
import sqlite3 as sql
import threading
from typing import Union, List, Tuple, Optional
import numpy as np
import os
import sys
import time
from helpers.utils import *
import json

# Auxiliar classes
from helpers.QueryResults import QueryResults

class SQLiteORM:

    def __init__(self, db_path: str):

        self.db_path = db_path
        self.db_name = db_path
        self.conn = None
        self.cursor = None
        self.query = None
        self.deleted_rows = 0
        self.stream_mode = False

    def get_database(self) -> str:

        if "db" in self.db_path: 
            return self.db_path
        return self.db_name

    def close_connection(self) -> None:

        self.conn.close()

    def connect_DB(self) -> Union[sql.Connection, None]:

        try:
            self.conn = sql.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sql.Row
            self.cursor = self.conn.cursor()
            self.cursor.execute("PRAGMA journal_mode=WAL;") # multi threading to avoid blocks of database
            print("✅ Connection success to database:", self.db_name.split('.')[-1])
            return self.conn
        except sql.Error as e:
            print(f"❌ Database error: {e}")
            return None

    def connect_stream_DB(self) -> Union[sql.Connection, None]:
        
        try:
            self.conn = sql.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sql.Row
            self.cursor = self.conn.cursor()

            print(f"Connecting to database {self.db_name} in eStream mode...")

            self.cursor.execute("PRAGMA synchronous = OFF;")
            self.cursor.execute("PRAGMA journal_mode = MEMORY;")
            self.cursor.execute("PRAGMA temp_store = MEMORY;")

            self.cursor.execute("PRAGMA locking_mode = EXCLUSIVE;")

            self.cursor.execute("PRAGMA foreign_keys = OFF;")

            self.cursor.execute("PRAGMA cache_size = -2000000;")

            self.cursor.execute("PRAGMA automatic_index = OFF;")
            self.cursor.execute("PRAGMA cache_spill = OFF;")

            print("⚡ eStream mode active! Ultra-fast performance enabled.")
            self.stream_mode = True
            return self.conn

        except sql.Error as e:
            print(f"❌ eStream connection error: {e}")
            return None

    def close_connection_stream_DB(self):
        
        try:
            print("Closing eStream connection and restoring normal mode...")

            self.cursor.execute("PRAGMA foreign_keys = ON;")
            self.cursor.execute("PRAGMA journal_mode = WAL;")
            self.cursor.execute("PRAGMA synchronous = NORMAL;")
            self.cursor.execute("PRAGMA locking_mode = NORMAL;")
            self.cursor.execute("PRAGMA automatic_index = ON;")
            self.cursor.execute("PRAGMA cache_spill = ON;")

            print(f"Database {self.db_name} closed and returned to stable normal mode.")
            self.conn.close()
            self.stream_mode = False
            return True

        except sql.Error as e:
            print(f"❌ Error restoring normal mode: {e}")
            return False

    def is_text_column(self, table_name, column):

        info = self.execute_query(f"PRAGMA table_info({table_name})").json

        for col in info:
            if col["name"] == column:
                ctype = col["type"].upper()
                if any(t in ctype for t in ("CHAR", "TEXT", "CLOB", "VARCHAR")):
                    return True
                return False

        raise Exception(f"Column '{column}' not found in table '{table_name}'")

    def get_sqlite_type(self, value) -> str:

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

        # Special types
        import datetime, decimal, uuid, json

        if isinstance(value, (datetime.date, datetime.datetime)):
            return "TEXT"  # ISO format recommended

        if isinstance(value, decimal.Decimal):
            return "NUMERIC"

        if isinstance(value, uuid.UUID):
            return "TEXT"

        if isinstance(value, (list, dict)):
            return "TEXT"  # Save as JSON

        # Every other kind: save as text
        return "TEXT"

    def get_pk(self, table_name: str) -> list:

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

    def check_table(self, table_name: str) -> bool:
        
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
    def insert_many(self, table_name: str, items: list):
        """
        Insert multiple rows:
        items = [
            (v1, v2, v3, ...),
            (v1, v2, v3, ...),
        ]
        """

        try:
            if not items:
                raise Exception("items is empty, there are not rows to insert.")

            # ==========================
            # 1. COLUMNAS DE LA TABLA
            # ==========================
            columns = self.check_columns(table_name)
            if not columns:
                raise Exception(f"It could not be obtained columns from {table_name}")

            # ==========================
            # 2. PRIMARY KEY
            # ==========================
            info = self.get_object_columns(table_name)
            if not info:
                raise Exception(f"It could not be obtained table_info PRAGMA from '{table_name}'")

            primary_keys = [col["name"] for col in info if col["pk"] == 1]

            cols_to_insert = [c for c in columns if c not in primary_keys]

            if not cols_to_insert:
                raise Exception(
                    f"'{table_name}' table does not have recorded columns (Only for a primary key)."
                )

            # ==========================
            # 3. VALIDACIÓN DE FILAS
            # ==========================
            expected_cols = len(cols_to_insert)

            for row in items:
                if len(row) != expected_cols:
                    raise Exception(
                        f"Row {row} has {len(row)} values but awaited for {expected_cols}: {cols_to_insert}"
                    )

            # ==========================
            # 4. QUERY PREPARADA
            # ==========================
            placeholders = ", ".join(["?"] * expected_cols)
            base_query = (
                f"INSERT INTO {table_name} ({', '.join(cols_to_insert)}) "
                f"VALUES ({placeholders})"
            )

            # ==========================
            # 5. PRAGMA TURBO
            # ==========================
            self.activate_stream()

            # ==========================
            # 6. CHUNK SIZE INTELIGENTE
            # ==========================
            chunk_size = auto_chunk_size(items, mode="sqlite")
            total = len(items)

            print(f"INSERT MANY INIT ({total} rows)…")
            print(f"✔ Recorded columns: {cols_to_insert}")
            print(f"✔ Chunk size: {chunk_size:,}")

            # ==========================
            # 7. INSERT POR BLOQUES
            # ==========================
            for start in range(0, total, chunk_size):
                chunk = items[start : start + chunk_size]
                self.execute_query(base_query, chunk)
                print(f"   → Recorded {start + len(chunk)}/{total}")

            # ==========================
            # 8. RESTAURAR PRAGMAS
            # ==========================
            self.desactivate_stream()

            print("✅ INSERT MANY DONE")
            return True

        except Exception as e:
            print("❌ insert_many error:", e)
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

    # ========================
    # DELETE RECORDS
    # ========================
    def delete(self, data: Union[list, int] = None, table_name: str = "") -> bool:

        try:

            row_count = 0

            self.activate_stream()

            # Validate table
            if not self.check_table(table_name):
                raise Exception(f"Table '{table_name}' does not exist")

            # Obtain primary key
            primary_keys = self.get_pk(table_name)

            if len(primary_keys) == 0:
                raise Exception("Table has no primary key — cannot perform delete by ID.")

            if len(primary_keys) > 1:
                raise Exception( f"Table has multiple primary keys. Choose one: {', '.join(pk['name'] for pk in primary_keys)}")

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
            elif (
                isinstance(data, list)
                and len(data) == 3
                and isinstance(data[0], str)
                and data[1].upper() in ("=", ">", "<", "<>", "!=", ">=", "<=")
                and isinstance(data[2], (int, float, str))
            ):
                column, op, value = data
                where = f" WHERE {column} {op} ?"
                params = (value,)

                row_count = self.processing_stream(table=table_name, column=column, operator=op, value=value)

            # --- LIKE ---
            elif (
                isinstance(data, list)
                and len(data) == 3
                and isinstance(data[0], str)
                and data[1].upper() == "LIKE"
                and isinstance(data[2], str)
            ):
                column, op, value = data

                op = op.upper()

                type_value = self.get_sqlite_type(value)

                if type_value.upper() not in ("TEXT", "VARCHAR", "CHAR"):
                    raise Exception(f"Column '{column}' is type '{type_value}', cannot use {op}")

                if not self.is_text_column(table_name, column):
                    raise Exception(f"Cannot use {op} on non-text column '{column}' (type: {type_value})")
                    
                where = f" WHERE {column} {op} ?"
                params = (value,)

            # --- BETWEEN ---
            elif (
                isinstance(data, list)
                and len(data) == 3
                and isinstance(data[0], str)
                and data[1].upper() == "BETWEEN"
                and isinstance(data[2], (list,tuple))
                and len(data[2]) == 2
            ):
                column, op, (v1, v2) = data[0], data[1], data[2]
                where = f" WHERE {column} {op.upper()} ? AND ?"
                params = (v1, v2)

            elif isinstance(data, list) and len(data) > 0:
                # Validar tipos
                wrong_ids = []

                # Stream delete
                for item in data:
                    print(f"Processing id ({item})")
                    if self.get_sqlite_type(item) != type_primary_key:
                        print(f"Error processing id {item}")
                        wrong_ids.append(item)

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

            if row_count == 0:
                print("No rows found to delete with the provided criteria.")
                return False

            query = f"DELETE FROM {table_name}{where}"

            self.execute_query(query, params)

            print("✅ Delete successful")

            self.desactivate_stream()

            print(f"Rows deleted: {row_count if isinstance(data, list) else 1}")

            if row_count > 50000:
                print("🛠️  Performing VACUUM to optimize database after large delete...")
                self.execute_query("VACUUM;")
                print("✅ VACUUM completed.")

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

    def processing_stream(self, **statements) -> int:

        table_name, column, operator, value = list(statements.values())
        ids = self.execute_query(f"SELECT {column} FROM {table_name} WHERE {column} {operator} ?", (value,)).json
        print(f"   → Found {len(ids)} rows to process.")
        total_ids = len(ids)
        percentage_step = max(total_ids // 10, 1)
        for idx in range(total_ids):
            if (idx + 1) % percentage_step == 0 or (idx + 1) == total_ids:
                percent_complete = ((idx + 1) / total_ids) * 100
                print(f"   → Processed {idx + 1}/{total_ids} ({percent_complete:.1f}%)")
                time.sleep(0.04)  # Simulate processing time

        return total_ids

    # =======================
    # ADDITIONAL METHODS
    # =======================
    def reset_autoincrement(self, table_name: str) -> bool:

        """
        Reset AUTOINCREMENT counter for a specific table.
        """
        try:
            self.cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}';")
            self.conn.commit()
            print(f"✅ AUTOINCREMENT reset for table '{table_name}'")
            return True
        except sql.Error as e:
            print(f"⚠️ Error resetting autoincrement for table '{table_name}': {e}")
            return False
            
    def reset_autoincrements(self) -> bool:

        """
        Reset AUTOINCREMENT counter for all tables.
        """
        try:
            self.cursor.execute("DELETE FROM sqlite_sequence;")
            self.conn.commit()
            print(f"✅ AUTOINCREMENT reset for all tables")
            return True
        except sql.Error as e:
            print(f"⚠️ Error resetting autoincrement for all tables: {e}")
            return False

    def activate_stream(self) -> None:

        if self.stream_mode:
            print("eStream mode is already active.")
            self.cursor.execute("PRAGMA synchronous = OFF;")
            self.cursor.execute("PRAGMA journal_mode = MEMORY;")
            self.cursor.execute("PRAGMA temp_store = MEMORY;")
            self.cursor.execute("PRAGMA locking_mode = EXCLUSIVE;")
            self.cursor.execute("PRAGMA foreign_keys = OFF;")
            self.cursor.execute("PRAGMA cache_size = -2000000;")
    
    def desactivate_stream(self) -> None:

        if self.stream_mode:
            print("eStream mode is already deactivated.")
            self.cursor.execute("PRAGMA foreign_keys = ON;")
            self.cursor.execute("PRAGMA journal_mode = WAL;")
            self.cursor.execute("PRAGMA synchronous = NORMAL;")
    
        
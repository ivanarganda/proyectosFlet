import sqlite3 as sql
import threading
from typing import Union, List, Tuple, Optional
import numpy as np
import os
import re
import sys
import time
from helpers.utils import *
import datetime, decimal, uuid, json

# Auxiliar classes
from helpers.QueryResults import QueryResults

class TypeData(Exception):
    pass

__all__ = [

    "SQLiteORM",
    "integer", "text", "floating", "numeric", "varchar", "boolean","enum"

]

SQLITE_FUNCS = ["CURRENT_DATE", "CURRENT_TIME", "CURRENT_TIMESTAMP"]

def _build_type_declaration(base_type: str, **kwargs) -> Union[str, bool]:

    pk             = kwargs.get("pk", False)

    autoincrement  = kwargs.get("autoincrement", False)

    not_null       = kwargs.get("not_null", False)

    default        = kwargs.get("default", None)

    enum_values    = kwargs.get("enum_values", None)

    size           = kwargs.get("size", None)

    unique         = kwargs.get("unique", False)

    fk             = kwargs.get("fk", None)

    def add_common_options(options: list):

        nonlocal default

        if not_null:      options.append("NOT_NULL")

        if pk:            options.append("PRIMARY_KEY")

        if autoincrement: options.append("AUTOINCREMENT")

        if unique:        options.append("UNIQUE")

        if default is not None:

            # Clone value to avoid mutating original
            default_value = default

            # Check if it's a TEXT literal and not a SQLite function
            if isinstance(default_value, str) and not default_value.upper() in SQLITE_FUNCS:

                default_value = f"'{default_value}'"

            options.append(f"DEFAULT({default_value})")

        return options

    # ============================================
    # 4. Validación para tipos numéricos
    # ============================================
    def validate_numeric(type_):

        if size is not None:

            raise ValueError(json.dumps({
                "message": f"SQLite {type_} type does NOT support size.",
                "value": size,
                "base_type": type_
            }))

        if default is not None:

            # INTEGER cannot accept float or str
            if type_ == "INTEGER" and isinstance(default, (str, float)):

                raise ValueError(json.dumps({
                    "message": "SQLite INTEGER cannot use string or float as DEFAULT",
                    "value": default,
                    "base_type": type_
                }))

            # REAL must not accept strings
            if type_ == "REAL" and isinstance(default, str):

                raise ValueError(json.dumps({
                    "message": "SQLite REAL cannot use string as DEFAULT",
                    "value": default,
                    "base_type": type_
                }))

    # ============================================
    # 5. Validación para TEXT / DATE
    # ============================================
    def validate_text_date(type_):

        if size is not None:

            raise ValueError(json.dumps({
                "message": f"SQLite {type_} does NOT support size",
                "value": size,
                "base_type": type_
            }))
    
    def validate_varchar(type_):

        nonlocal size, default

        if size is None:

            raise ValueError(json.dumps({
                "message": "SQLite VARCHAR requires a size parameter",
                "value": size,
                "base_type": type_
            }))

        if not isinstance(size, int) or size <= 0:

            raise ValueError(json.dumps({
                "message": "SQLite VARCHAR size must be a positive integer",
                "value": size,
                "base_type": type_
            }))
        
        if default is not None:

            if isinstance(default, str) and default.upper() in SQLITE_FUNCS:

                return  # es una función válida de SQLite
            
            if isinstance( default , str ):

                clean_default = default.strip("'").strip('"')
                if len(clean_default) > size:
                    raise ValueError(json.dumps({
                        "message": f"SQLite VARCHAR default value exceeds defined size of {size}",
                        "value": default,
                        "base_type": type_
                    }))
    
    def validate_boolean(type_):

        if size is not None:

            raise ValueError(json.dumps({
                "message": f"SQLite BOOLEAN does NOT support size",
                "value": size,
                "base_type": type_
            }))

        if default is not None:

            if not isinstance(default, int) or default not in (0, 1):

                raise ValueError(json.dumps({
                    "message": "SQLite BOOLEAN default must be 0 or 1",
                    "value": default,
                    "base_type": type_
                }))
    
    def validate_enum(type_):

        nonlocal enum_values

        if default is not None and default not in enum_values:

            raise ValueError(json.dumps({
                "message": f"SQLite ENUM default must be among that values {", ".join(enum_values)}",
                "value": default,
                "base_type": type_
            }))

    options = [base_type]

    if base_type in ("INTEGER", "REAL", "NUMERIC"):

        validate_numeric(base_type)

        options = add_common_options(options)

    elif base_type in ("TEXT", "DATE"):

        validate_text_date(base_type)

        options = add_common_options(options)
    
    elif base_type == "VARCHAR":

        validate_varchar(base_type)

        # Optain position varchar
        pos_varchar = options.index("VARCHAR")

        options[pos_varchar] = f"VARCHAR({size})"

        options = add_common_options(options)
    
    elif base_type == "BOOLEAN":

        # SQLite does not have a separate BOOLEAN type, use INTEGER
        base_type = "INTEGER"

        validate_boolean(base_type)

        options = add_common_options(options)
    
    elif base_type == "ENUM":

        if enum_values:

            cleaned = []

            for val in enum_values:

                if isinstance(val, str):

                    cleaned.append(f"'{val}'")

                else:

                    cleaned.append(str(val))
            
            check_sql = f"CHECK( IN ({', '.join(cleaned)}))"

            options.append(check_sql)

            validate_enum(base_type)

            options = add_common_options(options)

    else:

        raise TypeError(f"Unsupported SQLite type: {base_type}")

    # ============================================
    # 7. Reordenar opciones limpia y correctamente
    # ============================================
    protected = []

    for opt in options:

        if opt.startswith("DEFAULT("):

            protected.append(opt)  # lo dejamos intacto

        else:

            protected.append(opt.replace("_", " "))

    options = protected

    # ============================================
    # 8. Formatear salida
    # ============================================
    formatted = " ".join(options)

    return formatted

def build_type(type_name: str, **kwargs):

    try:

        return _build_type_declaration(type_name, **kwargs)

    except ValueError as ve:

        data = json.loads(str(ve))

        msg = data.get("message", "")

        val = data.get("value", "")

        bt  = data.get("base_type", type_name)

        print(f"⚠️ {msg} Given: {val} for base type: {bt}")

        if bt in ("ENUM"):

            raise Exception(f"⚠️ {msg} Given: {val} for base type: {bt}")

        # formatear salida final
        if isinstance(bt, str):

            return bt.replace("_", " ").strip()

        return str(bt)

    except TypeData as e:

        print(f"⚠️ Unexpected error: {e}")

        return type_name
    
    except Exception as e:

        print( e )

def boolean(**kwargs):

    # SQLite does not have a separate BOOLEAN type, use INTEGER as numeric type
    return numeric(**kwargs)

def integer(**kwargs):

    return build_type("INTEGER", **kwargs)

def floating(**kwargs):

    return build_type("REAL", **kwargs)

def text(**kwargs):

    return build_type("TEXT", **kwargs)

def varchar(**kwargs):

    return build_type("VARCHAR", **kwargs)

def numeric(**kwargs):

    base_type = "NUMERIC"

    if "default" in kwargs:

        default = kwargs["default"]

        regex_int = r"^-?\d+$"

        regex_float = r"^-?\d+\.\d+$"

        regex_cientific = r"^-?\d+(\.\d+)?[eE][-+]?\d+$"

        regex_date = r"^\d{4}-\d{2}-\d{2}$"

        # Comprobación del default
        if default is None:

            type_ = "NUMERIC"

        elif re.match(regex_int, str(default)):

            type_ = "INTEGER"

        elif re.match(regex_float, str(default)) or re.match(regex_cientific, str(default)):

            type_ = "REAL"
        
        elif re.match(regex_date, str(default)):
            
            type_ = "DATE"  # SQLite almacena fechas como texto

        else:

            type_ = "TEXT"
    
    base_type = type_

    return build_type(base_type, **kwargs)

def enum(**kwargs):

    enum_values = kwargs.get("enum_values", None)

    if not isinstance(enum_values, (list, tuple)) or len(enum_values) == 0:

        raise ValueError("ENUM requires a non-empty list of values")

    # Guardar los valores para validación

    return build_type("ENUM", **kwargs)

class SQLiteORM:

    def __init__(self, db_path: str):

        self.db_path = db_path
        
        self.db_name = db_path
        
        self.conn = None
        
        self.cursor = None
        
        self.query = None
        
        self.deleted_rows = 0
        
        self.stream_mode = False
    
    """
        DATABASE CONNECTION FUNCTIONS: close_connection, connect_DB, connect_stream_DB, close_connection_stream_DB
        DESCRIPTION: These methods handle the connection to the SQLite database, including standard and eStream modes.
        
    """

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

    """
        DATABASE DML FUNCTIONS: insert, insert_many, select_all, select_one, select_where, 
            select_columns, select_by_id, select_like, select_in, update_all, update, delete_all, delete
        DESCRIPTION: These methods provide basic CRUD operations for interacting with the SQLite database.
    """
    # ===============================
    # INSERT ORM ( insert both single values and many values)
    # ===============================
    def insert_many(self, table_name: str, items: list):

        try:

            if not items:

                raise Exception("items is empty, there are not rows to insert.")

            # ==========================
            # 1. TABLE COLUMNS
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
            # 3. VALIDATE ROWS LENGTH
            # ==========================
            expected_cols = len(cols_to_insert)

            for row in items:

                if len(row) != expected_cols:

                    raise Exception(

                        f"Row {row} has {len(row)} values but awaited for {expected_cols}: {cols_to_insert}"

                    )

            # ==========================
            # 4. PREPARED QUERY
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
            # 6. CHUNK SIZE INTELLIGENT
            # ==========================
            chunk_size = auto_chunk_size(items, mode="sqlite")

            total = len(items)

            print(f"INSERT MANY INIT ({total} rows)…")

            print(f"✔ Recorded columns: {cols_to_insert}")

            print(f"✔ Chunk size: {chunk_size:,}")

            # ==========================
            # 7. INSERT BY CHUNKS
            # ==========================
            for start in range(0, total, chunk_size):

                chunk = items[start : start + chunk_size]

                self.execute_query(base_query, chunk)

                print(f"   → Recorded {start + len(chunk)}/{total}")

            # ==========================
            # 8. RESTAURE PRAGMAS
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
    # UPDATE ALL RECORDS
    # ========================
    def update_all(self, set_values: dict, table_name: str) -> bool:
        
        return self.update(set_values=set_values, table_name=table_name)
        
    # ========================
    # UPDATE RECORDS
    # ========================
    def update(self, set_values=dict, data: Union[str,list, int] = None, table_name: str = "") -> bool:

        try:

            self.activate_stream()

            # Validate table
            if not self.check_table(table_name):

                raise Exception(f"Table '{table_name}' does not exist")

            # Build WHERE clause
            where, params, row_count = list(self._build_where_clause(data=data, table=table_name).values())

            print( f"{where} {params} {row_count} ")

            # check if keys of set values are valid columns
            valid_columns = self.check_columns(table_name)

            for col in set_values.keys():

                if col not in valid_columns:

                    raise Exception(f"Column '{col}' does not exist in table '{table_name}'")

            query = f"UPDATE {table_name} SET {self._build_set_clause(set_values)}{where}"

            self.query = query

            print(f"Executing update: {self.formatted_query()} with params {tuple(set_values.values()) + params}")
            
            self.execute_query(query, tuple(set_values.values()) + params)

            print("✅ Update successful")

            return True

        except Exception as e:

            print(f"Error: {e}")
            
            return False

    # ========================
    # DELETE ALL RECORDS
    # ========================
    def delete_all(self, table_name: str) -> bool:

        return self.delete(table_name=table_name)

    # ========================
    # DELETE RECORDS
    # ========================
    def delete(self, data: Union[list, int] = None, table_name: str = "") -> bool:

        try:

            self.activate_stream()

            # Validate table
            if not self.check_table(table_name):

                raise Exception(f"Table '{table_name}' does not exist")

            # Build WHERE clause
            where, params, row_count = list(self._build_where_clause(data=data, table=table_name).values())

            if row_count == 0:

                print("No rows found to delete with the provided criteria.")

                return False

            query = f"DELETE FROM {table_name}{where}"

            self.query = query

            print(f"Executing delete: {self.formatted_query()} with params {params}")
    
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
    
    """

        DEFINITION DATA LANGUAGE FUNCTIONS: create_table, drop_table, alter_table
        DESCRIPTION: These methods handle DDL operations for managing database schema.
        
        # ======================== EXAMPLE USAGE ========================
        db.create_table(
            "productos",
            columns={
                "id": integer(pk=True, autoincrement=True),
                "nombre": text(not_null=True),
                "precio": real(default=0),
                "activo": boolean(default=1),
                "id_marca": integer(fk=("marcas", "id"))
            }
        )

    """
    def create_table(self, table_name: str, columns: dict= None, foreign_keys: dict= None ) -> bool:

        try:

            if not columns or not isinstance(columns, dict):

                raise ValueError("Data must be a non-empty list of column definitions.")

            col_defs = []
            col_names = []

            for col_name, opts in columns.items():

                col_def = col_name + " " + opts

                if "CHECK(" in opts and "ENUM" in opts:

                    col_def = col_def.replace("CHECK(", f"CHECK({col_name} ", 1)

                col_defs.append(col_def)

                if foreign_keys:

                    col_names.append( col_name )

            header_create_table = f"CREATE TABLE IF NOT EXISTS {table_name}"

            body_options_create_table = f"{",\n".join(col_defs)}"

            relations_foreign_keys = ""

            # Check foreign_keys
            if len(col_names) != 0:
                
                print( col_names )

            query = f"{header_create_table} ({body_options_create_table}{relations_foreign_keys})" 

            return True

        except sql.Error as e:

            print(f"⚠️ Create table error: {e}")

            return False
        
        except ValueError as ve:

            print(f"⚠️ Value error: {ve}")

            return False

    """

        ADDITIONAL METHODS: fetch_all, fetch_one, fetch_many, date, time, datetime, format_table, formatted_query, 
            format_results, processing_stream, _build_placeholders, _build_set_clause, _build_where_clause, execute_query, 
            reset_autoincrement, reset_autoincrements, activate_stream, desactivate_stream, is_text_column, get_database, 
            get_sqlite_type, get_pk, get_query, get_object_columns, check_columns, check_table
        
        DESCRIPTION: These methods provide additional functionalities for fetching results, formatting outputs,
            building SQL clauses, executing queries, managing autoincrement values, and checking database schema.
            
    """
    # =======================
    # ADDITIONAL METHODS
    # =======================  
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

    def date(self) -> str:

        # Return current date in YYYY-MM-DD format
        return SQLITE_FUNCS[0]
    
    def time(self) -> str:

        # Return current time in HH:MM:SS format
        return SQLITE_FUNCS[1]
    
    def datetime(self) -> str:

        # Return current date and time in YYYY-MM-DD HH:MM:SS format
        return SQLITE_FUNCS[2]

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

    def _build_placeholders(self, length: int) -> str:

        return ", ".join(["?"] * length)

    def _build_set_clause(self, set_values: dict) -> str:

        set_clauses = [f"{col} = ?" for col in set_values.keys()]

        return ", ".join(set_clauses)

    def _build_where_clause(self, **args) -> dict[str, Union[str, int, list, tuple]]:

        # Obtain primary key
        print( f"Building WHERE clause with args: {args} " )

        data, table_name = list(args.values())

        primary_keys = self.get_pk(table_name)

        where = ""

        params = ()

        row_count = 0

        if len(primary_keys) == 0:

            raise Exception("Table has no primary key — cannot perform delete by ID.")

        if len(primary_keys) > 1:

            raise Exception( f"Table has multiple primary keys. Choose one: {', '.join(pk['name'] for pk in primary_keys)}")

        name_primary_key = primary_keys[0]["name"]

        type_primary_key = primary_keys[0]["type"]

        if data is not None:
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
            
            elif (
                isinstance(data, list)
                and len(data) == 3
                and isinstance(data[0], str)
                and data[1].upper() == "IN"
                and isinstance(data[2], (list,tuple))
            ):
                column, op, values = data[0], data[1], data[2]

                where = f" WHERE {column} {op.upper()} ({', '.join(['?'] * len(values))})"

                params = tuple(values)

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
        
        return {"where": where, "params": params , "row_count": row_count }
    
    def execute_query(self, query: str, params: Union[tuple, list, None]=None) -> Union[list, bool]:

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

    def is_text_column(self, table_name, column):

        info = self.execute_query(f"PRAGMA table_info({table_name})").json

        for col in info:

            if col["name"] == column:

                ctype = col["type"].upper()

                if any(t in ctype for t in ("CHAR", "TEXT", "CLOB", "VARCHAR")):

                    return True

                return False

        raise Exception(f"Column '{column}' not found in table '{table_name}'")

    def get_database(self) -> str:

        if "db" in self.db_path: 
            
            return self.db_path

        return self.db_name

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
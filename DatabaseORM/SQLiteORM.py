import sqlite3 as sql
from typing import Union, List, Tuple, Optional
import os

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

    def check_columns(self, table_name: str) -> Union[list, None]:
        try:
            self.cursor.execute(f"PRAGMA table_info({table_name});")
            columns_info = self.cursor.fetchall()
            columns = [col['name'] for col in columns_info]
            return columns
        except sql.Error as e:
            print(f"⚠️ Error fetching columns for {table_name}: {e}")
            return None

    def insert_many_single_query(self, data: list[tuple], table_name: str) -> bool:
        try:
            # 1. Columnas reales
            columns = self.check_columns(table_name)

            # 2. Crear valores en texto SQL
            values_sql = []
            for row in data:
                formatted = []
                for val in row:
                    # Convertir a SQL-safe literal
                    if isinstance(val, str):
                        formatted.append(f'"{val}"')
                    elif val is None:
                        formatted.append("NULL")
                    else:
                        formatted.append(str(val))
                values_sql.append("(" + ", ".join(formatted) + ")")
            
            db.execute_query(
                """
                PRAGMA synchronous = OFF;
                PRAGMA journal_mode = MEMORY;
                PRAGMA temp_store = MEMORY;
                PRAGMA foreign_keys = OFF;
                """
            )

            # 3. Construir query grande
            query = (
                f"INSERT OR IGNORE INTO {table_name} "
                f"({', '.join(columns)}) VALUES\n" +
                ",\n".join(values_sql)
            )

            db.execute_query(query)

            print("✅ Insert masivo con único query completo.")

            db.execute_query(
                """ 
                PRAGMA synchronous = FULL;
                PRAGMA journal_mode = WAL;
                PRAGMA foreign_keys = ON;
                """
            )

            return True

        except Exception as e:
            print("❌ Error en insert_many_single_query:", e)
            self.conn.rollback()
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

    def execute_query(self, query: str, params: Union[tuple, list, None]=None) -> Union[list, bool]:
        try:
            self.query = query

            if params is None:
                self.cursor.execute(query)

            elif isinstance(params, list):
                
                if all(isinstance(p, (list, tuple)) for p in params):
                    self.cursor.executemany(query, params)
                else:
                    raise ValueError("Params must be a list of tuples or lists for executemany().")

            else:
                self.cursor.execute(query, params)

            self.conn.commit()

            cmd = query.lstrip().split()[0].upper()

            if cmd in ("SELECT", "PRAGMA", "WITH"):
                return self.cursor.fetchall()

            return True

        except sql.Error as e:
            print(f"⚠️ Query error: {e}")
            return False

    def select_all(self, table: str):

        query = f"SELECT * FROM {table}"
        return self.execute_query(query)

    def select_one(self, table: str, **conditions):

        if not conditions:
            raise ValueError("select_one requires at least one condition.")

        where = " AND ".join(f"{col} = ?" for col in conditions)
        params = tuple(conditions.values())

        query = f"SELECT * FROM {table} WHERE {where} LIMIT 1"
        result = self.execute_query(query, params)
        return result[0] if result else None

    def select_where(self, table: str, **conditions):

        where = " AND ".join(f"{col} = ?" for col in conditions)
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


    def close_connection(self) -> None:

        self.conn.close()

    def get_query(self) -> str:
        
        return self.query
import sqlite3 as sql

import os

DB_PATH = os.path.join(os.path.dirname(__file__) , "forecast.db")

class Database:

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.query = None

    def get_db(self,g):
        if "db" not in g:
            g.db = sql.connect(DB_PATH, check_same_thread=False)
            g.db.row_factory = sql.Row
        return g.db

    def conect_DB(self):
        try:
            self.conn = sql.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sql.Row
            self.cursor = self.conn.cursor()
            print("✅ Connection success")
            return self.conn
        except sql.Error as e:
            print(f"❌ Database error: {e}")
            return None

    def execute_query(self, query, params = ()):
        try:
            self.query = query
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.conn.commit()
            return True
        except sql.Error as e:
            print(f"⚠️ Query error: {e}")
            return False

    def reset_autoincrement(self, table_name, delete_rows=False):
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

    def fetch_all(self):

        rows = self.cursor.fetchall()

        results = [dict(row) for row in rows]

        return results

    def close_connection(self):
        self.conn.close()

    def get_query(self):
        
        return self.query
import sqlite3 as sql
from conf.DB import Database
import os

from dotenv import load_dotenv
from helpers.utils import get_queries

load_dotenv()

user_admin = os.getenv("ADMIN_USER")
email_admin = os.getenv("ADMIN_EMAIL")
password_admin = os.getenv("PASSWORD_USER")

def init_connection( db ):

    try:
    
        db.conect_DB()
        print("✅ Db connected successfully")
        
        return True

    except sql.Error as e:

        print("❌ SQLite error:", e)

        return False

def init_tables( db ):
    
    try:

        if db.conn:

            if ( db.execute_query( get_queries()["create_roles_table"] ) ):
                print("✅ Created roles table successfully")
            
            if ( db.execute_query( get_queries()["init_roles_data"] ) ):
                print("✅ Init dumped roles data from roles table")
            
            if ( db.execute_query( get_queries()["create_users_table"] ) ):
                print("✅ Created users table successfully")
            
            if ( db.execute_query( get_queries()["init_user_admin_data"] , ( user_admin , email_admin, password_admin ) ) ):
                print("✅ Init dumped admin user data from users table")
            
            if ( db.execute_query( get_queries()["create_tasks_categories_table"] ) ):
                print("✅ Created tasks categories table successfully")

            if ( db.execute_query( get_queries()["create_tasks_table"] ) ):
                print("✅ Created tasks table successfully")

            print(f"✅ Connected to {db.db_path} successfully")

            return True

        return False

    except sql.Error as e:

        print("❌ SQLite error:", e)

        return False

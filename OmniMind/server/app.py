import logging # TODO only for debug

import json
from flask import Flask, request, jsonify, g
from markupsafe import escape

import sqlite3 as sql
from conf.DB import Database
import os

from dotenv import load_dotenv
from helpers.utils import get_queries
from conf.conn import init_connection, init_tables

import datetime

logging.basicConfig(filename='process.log', level=logging.DEBUG)

load_dotenv()

user_admin = os.getenv("ADMIN_USER")
email_admin = os.getenv("ADMIN_EMAIL")
password_admin = os.getenv("PASSWORD_USER")

db = Database()

app = Flask(__name__)

def handle_server():

    if init_connection( db ) == False: raise Exception("🤔 Something went wrong in the server!!")

def parse_json_response( message , status = 200 ):

    return jsonify(
            message=message,
            status=status
        )
    
def check_authorization(headers):
    
    try:
    
        auth_header = headers.get("Authorization", None)
        if not auth_header:
            return False

        if "Bearer" not in auth_header:
            return False
        
        # Obtain token
        token = auth_header.split(" ")[1]
        if not token:
            return False

        # Validate token
        db.execute_query(
            """
                SELECT * from users where token = ?
            """,
            (token,)
        )

        result = db.fetch_all()
        if not result:
            return False

        return True
    
    except IndexError:
        return False

# Define routes outside of __main__ block
@app.route("/roles", methods=["GET"])
def get_roles():

    try:

        handle_server()
        
        # Check autorization header
        try:
            authorized = check_authorization( request.headers )
            if authorized != True: raise Exception( "Unauthorized" )
        except Exception as e:
            return parse_json_response( str(e) , 301 )

        db.execute_query(
            """ 
                SELECT * from roles
            """
        )

        result = db.fetch_all()

        return parse_json_response( result )

    except Exception as e:

        return parse_json_response( str(e) , 400 )

@app.route("/users", methods=["GET"])
def get_users():

    try:

        handle_server()
        
        # Check autorization header
        try:
            authorized = check_authorization( request.headers )
            if authorized != True: raise Exception( "Unauthorized" )
        except Exception as e:
            return parse_json_response( str(e) , 301 )

        # If token is valid, proceed to fetch users
        db.execute_query(
            """ 
                SELECT * from users
            """
        )

        result = db.fetch_all()

        return parse_json_response( result )

    except Exception as e:
        
        return parse_json_response( str(e) , 400 )

@app.route("/users/register", methods=["POST"])
def register():

    try:

        handle_server()

        json_data = request.json

        # logging.debug(json_data) 

        username = json_data.get("username", None )
        email = json_data.get("email", None )
        password = json_data.get("password", None )

        if username == None or email == None or password == None:
            return parse_json_response( "Incorrect credentials" , 400 )

        db.execute_query(
            """ 
                SELECT * from users where username = ? or email = ?
            """,
            ( username, email )
        )

        # logging.debug(db.get_query())

        result = db.fetch_all()

        # logging.debug(result)

        if result:
            return parse_json_response( f"User {username} or email {email} is already taken" , 401 )

        db.execute_query(
            """ 
                INSERT INTO users ( username, email , password, role, token ) VALUES ( ? , ? , ? , ? , ? )
            """,
            ( username , email, password , 2 , None )
        )

        logging.debug(db.get_query())

        db.close_connection()

        return parse_json_response("User registered successfully", 200)

    except Exception as e:

        logging.debug(e)
        
        return parse_json_response( str(e) , 400 ) 

@app.route("/users/update/<id_user>", methods=["PUT"])
def update():

    try:

        handle_server()

        json_data = request.json

        # logging.debug(json_data) 

        id_user = request.args.get('id_user')

        username = json_data.get("username", None )
        email = json_data.get("email", None )
        password = json_data.get("password", None )

        db.execute_query(
            """ 
                SELECT * from users where id = ?
            """,
            ( id_user, )
        )

        # logging.debug(db.get_query())

        result = db.fetch_all()

        if username == None: 
            username = result[0]["username"]
            
        if email == None: 
            email = result[0]["email"]

        if password == None: 
            password = result[0]["password"]

        db.execute_query(
            f""" 
                UPDATE users SET username = ?, email = ? , password = ? where id = {id_user} )
            """,
            ( username , email,  password )
        )

        logging.debug(db.get_query())

        db.close_connection()

        return parse_json_response("User updated successfully", 200)

    except Exception as e:

        logging.debug(e)
        
        return parse_json_response( str(e) , 400 ) 

@app.route("/users/login", methods=["POST"])
def login():

    try:

        handle_server()

        json_data = request.json

        # logging.debug(json_data) 

        email = json_data.get("email", None )
        password = json_data.get("password", None )

        if email == None or password == None:
            return parse_json_response( "Incorrect credentials" , 400 )

        db.execute_query(
            """ 
                SELECT id, username, email,password from users where email = ?
            """,
            ( email, )
        )

        # logging.debug(db.get_query())

        result = db.fetch_all()

        # logging.debug(result) 

        if not result:
            return parse_json_response( f"User {email} does not exist" , 402 )

        password_db = result[0]["password"]
        
        if password_db != password:
            return parse_json_response( "Incorrect password" , 401 )
        
        # To set payload for JWT token
        db.execute_query(
            """ 
               SELECT
                    u.id,
                    u.username,
                    u.email,
                    ( SELECT r.role from roles r where r.id = u.role ) as role
                from users u
                where u.email = ?
            """,
            ( email, )
        )

        # logging.debug(db.get_query())

        result = db.fetch_all()

        import jwt

        # Define a secret key
        secret_key = "secret"

        payload = result[0]
        
        payload["exp"] =  datetime.datetime.utcnow() + datetime.timedelta(hours=1)

        logging.debug(payload)

        encoded_jwt = jwt.encode(payload, secret_key, algorithm="HS256")
        
        db.execute_query(
            """ 
                UPDATE users SET token = ? where email = ?
            """,
            ( encoded_jwt , email )
        )

        return parse_json_response( 
            {
                "token": encoded_jwt
            } 
        )

    except Exception as e:

        logging.debug(e)
        
        return parse_json_response( str(e) , 400 )

# =========================
# TASK CATEGORIES ENDPOINTS
# =========================
@app.route("/tasks/categories", methods=["GET", "POST", "DELETE"])
def task_categories():
    try:
        if not init_connection(db):
            raise Exception("Database connection failed")

        # validar token
        authorized = check_authorization(request.headers)
        if not authorized:
            return parse_json_response("Unauthorized", 401)

        # obtener id_user desde token
        token = request.headers.get("Authorization").split(" ")[1]
        db.execute_query("SELECT id FROM users WHERE token = ?", (token,))
        user = db.fetch_all()
        if not user:
            raise Exception("User not found")
        id_user = user[0]["id"]

        # GET → obtener todas las categorías del usuario
        if request.method == "GET":
            db.execute_query(
                f"""SELECT tc.id, tc.category, tc.content, ( SELECT u.username from users u where u.id = tc.id_user ) FROM tasks_categories tc WHERE tc.id_user = ?", ({id_user},)"""
            )
            result = db.fetch_all()
            return parse_json_response(result, 200)

        # POST → crear una categoría
        if request.method == "POST":
            data = request.json
            category = data.get("category")
            content = data.get("content")
            if not category:
                raise Exception("Category name required")
            if not content:
                content = {}

            content_json = json.dumps(content)

            db.execute_query(
                "INSERT INTO tasks_categories (category, content, id_user) VALUES (?, ?, ?)",
                (category, content_json, id_user),
            )
            return parse_json_response("Category created successfully", 201)

        # DELETE → eliminar una categoría
        if request.method == "DELETE":
            data = request.json
            id_category = data.get("id")
            if not id_category:
                raise Exception("Category ID required")

            db.execute_query(
                "DELETE FROM tasks_categories WHERE id = ? AND id_user = ?",
                (id_category, id_user),
            )
            db.execute_query(
                "DELETE FROM tasks WHERE id_category = ? AND id_user = ?",
                (id_category, id_user),
            )
            return parse_json_response("Category deleted successfully", 200)

    except Exception as e:
        return parse_json_response(str(e), 400)

# ============
# TASKS ENDPOINTS
# ============
@app.route("/tasks", methods=["GET", "POST", "PUT", "DELETE"])
def tasks():
    try:
        if not init_connection(db):
            raise Exception("Database connection failed")

        authorized = check_authorization(request.headers)
        if not authorized:
            return parse_json_response("Unauthorized", 401)

        # obtener id_user desde token
        token = request.headers.get("Authorization").split(" ")[1]
        db.execute_query("SELECT id FROM users WHERE token = ?", (token,))
        user = db.fetch_all()
        if not user:
            raise Exception("User not found")
        id_user = user[0]["id"] 

        # GET → obtener todas las tareas del usuario
        if request.method == "GET":
            db.execute_query(
                """SELECT t.id, t.content
                   FROM tasks t 
                   LEFT JOIN tasks_categories c ON t.id_category = c.id 
                   WHERE t.id_user = ?""",
                (id_user,),
            )
            result = db.fetch_all()
            return parse_json_response(result, 200)

        # POST → crear nueva tarea
        if request.method == "POST":
            data = request.json
            task = data.get("task")
            content = data.get("content") 
            # @ format: 
            """
                {
                 "title": "title", 
                 "description": "description",
                 "date": datetime
                }

            """
            id_category = data.get("id_category")

            if not task:
                raise Exception("Task name required")
                
            if not content:
                content = {}

            content_json = json.dumps(content)

            db.execute_query(
                """INSERT INTO tasks (task, content, id_category, id_user) 
                   VALUES (?, ?, ?, ?)""",
                (task, content, id_category, id_user),
            )
            return parse_json_response("Task created successfully", 201)

        # PUT → actualizar tarea
        if request.method == "PUT":
            data = request.json
            id_task = data.get("id")
            task = data.get("task")
            content = data.get("content")
            id_category = data.get("id_category")

            if not id_task:
                raise Exception("Task ID required")

            db.execute_query(
                """UPDATE tasks 
                   SET task = ?, content = ?, id_category = ? 
                   WHERE id = ? AND id_user = ?""",
                (task, content, id_category, id_task, id_user),
            )
            return parse_json_response("Task updated successfully", 200)

        # DELETE → eliminar tarea
        if request.method == "DELETE":
            data = request.json
            id_task = data.get("id")
            if not id_task:
                raise Exception("Task ID required")

            db.execute_query(
                "DELETE FROM tasks WHERE id = ? AND id_user = ?",
                (id_task, id_user),
            )
            return parse_json_response("Task deleted successfully", 200)

    except Exception as e:
        return parse_json_response(str(e), 400)

if __name__ == "__main__":
    
    host = "0.0.0.0"
    port = 5000
    try:
        # initialize DB before running server
        handle_server()

        if init_tables( db ) == False: raise Exception("❌ unable intializing tables in database")
        
        print(f"Server is running and listening to {host}:{port}")

        app.run(host=host, port=port, debug=True)

    except Exception as e:

        print(e)

    except SyntaxError as e:

        print(e)
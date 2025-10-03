import logging # TODO only for debug

from flask import Flask, request, jsonify, g
from markupsafe import escape

import sqlite3 as sql
from conf.DB import Database
import os

from dotenv import load_dotenv
from helpers.utils import get_queries
from conf.conn import init_connection, init_tables

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


# Define routes outside of __main__ block
@app.route("/roles", methods=["GET"])
def get_roles():

    try:

        handle_server()

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
                SELECT * from users where username = ? and email = ?
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
                INSERT INTO users ( username, email , password, role ) VALUES ( ? , ? , ? , ? )
            """,
            ( username , email, password , 2 )
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
                SELECT * from users where email = ?
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

        import jwt

        # Define a secret key
        secret_key = "secret"

        payload = result[0]

        logging.debug(payload)

        encoded_jwt = jwt.encode(payload, secret_key, algorithm="HS256")

        return parse_json_response( 
            {
                "token": encoded_jwt
            } 
        )

    except Exception as e:

        logging.debug(e)
        
        return parse_json_response( str(e) , 400 )

if __name__ == "__main__":
    try:
        # initialize DB before running server
        handle_server()

        if init_tables( db ) == False: raise Exception("❌ unable intializing tables in database")

        app.run(host="0.0.0.0", port=5000, debug=True)
    
    except Exception as e:

        print(e)
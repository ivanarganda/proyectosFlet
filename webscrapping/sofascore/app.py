import os
import sys
import logging
import json
from flask import Flask, request, jsonify, g
from markupsafe import escape
import time
from dotenv import load_dotenv
from server.init_data import init_tables
from params import DB

import datetime

logging.basicConfig(filename='process.log', level=logging.DEBUG)

load_dotenv()

app = Flask(__name__)

db = None

def handle_server():

    db = SQLiteORM(DB)

    db.connect_DB()

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
        result = db.execute_query(
            """
                SELECT * from usuarios where token = ?
            """,
            (token,)
        ).json

        if not result:
            return False

        return True
    
    except IndexError:
        return False


if __name__ == "__main__":
    
    host = "0.0.0.0"
    port = 5000
    try:
        # initialize DB before running server
        handle_server()

        if init_tables() == False: raise Exception("❌ unable intializing tables in database")
        
        print(f"Server is running and listening to {host}:{port}")

        app.run(host=host, port=port, debug=True)

    except Exception as e:

        print(e)

    except SyntaxError as e:

        print(e)
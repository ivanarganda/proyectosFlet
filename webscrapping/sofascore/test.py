import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "DatabaseORM"))
from DatabaseORM.SQLiteORM import *
import re
import requests
from datetime import datetime
import time
from params import DB

db = SQLiteORM(DB)

db.connect_DB()

matches = [
    (438482, 2023, 1, 267, 87, 267000, '2023-08-11T17:30:00Z', 'FINISHED', 0, 2)
]

db.insert_many( 
    "partidos",
    matches
 )

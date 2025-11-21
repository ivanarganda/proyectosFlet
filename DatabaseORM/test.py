import os
import sys
from SQLiteORM import SQLiteORM as Database
import re

db = Database("productos.db")
db.conect_DB()

db.delete(data=[1],table_name="productos")

import os
import sys
from SQLiteORM import SQLiteORM as Database

db = Database("productos.db")
db.conect_DB()
import os
import sys
from SQLiteORM import SQLiteORM as Database
import re

db = Database("productos.db")

db.connect_stream_DB()
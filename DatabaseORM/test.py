import os
import sys
from SQLiteORM import SQLiteORM as Database
import re

db = Database("productos.db")

db.connect_DB()

# db.insert_many(
#     table_name="productos",
#     items=[
#         ('fsdfrg',4,'2021-01-01',1,2)
#         for _ in range(5000000)
#     ]
# )

# db.update(
#     set_values={'nombre': 'fedgrf', 'precio': 50},
#     data=["id_producto", "IN", (1,2,3)],
#     table_name='productos'
# )

# db.delete(
#     data=["id_producto", "IN", (4,5,6)],
#     table_name='productos'
# )
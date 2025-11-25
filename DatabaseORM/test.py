import os
import sys
from SQLiteORM import *
import re

db = SQLiteORM("productos.db")

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

db.create_table( 
    table_name="compras",
    columns={
        'id': integer(autoincrement=True, primary_key=True),
        'fecha_compra': numeric(default=db.datetime()),
        'status': enum(enum_values=['pending', 'completed', 'canceled'], default='pending', not_null=True),
        'id_producto': integer(not_null=True)
    },
    foreign_keys={
        'fk_orders_user': ("id_producto", "productos", "id_producto")
    }
)
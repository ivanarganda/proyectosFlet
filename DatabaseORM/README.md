# QuantumForge ORM

*A next-generation ultra-high-performance Python ORM forged for speed, streaming, and massive data operations.*

## 🚀 Overview
QuantumForge ORM is a high-performance Python ORM designed from the ground up to handle massive datasets, dynamic SQL, and extreme-speed operations using:
- Turbo PRAGMAs
- Intelligent chunking
- Streaming processors
- Dynamic WHERE builders
- Auto-optimizing DELETE, UPDATE and INSERT
- Full SQL flexibility with Python expressiveness

## ✨ Key Features
- Ultra-fast INSERT engine (5 million rows in ~5s)
- Intelligent chunk size detection
- Dynamic WHERE builder
- Streaming updates & deletes
- Type validation for primary keys
- LIKE, BETWEEN, IN, and all comparison operators
- Auto-VACUUM for massive deletes
- PRAGMA turbo mode
- Modular engines (SQLite, MySQL, Oracle)
- Mini-DSL for flexible filters
- 100% Python

## 🔥 Benchmarks
| Operation | Rows | Time |
|----------|------|------|
| Massive insert | 5,000,000 | ~5.7 seconds |
| Massive insert | 50,000,000 | ~50 seconds |
| Dynamic update | millions | < 0.5 seconds |
| Streaming delete | millions | instant + progress |

## 🛠 Installation
pip install quantumforge

## 🧱 Usage Examples

### 1. Connect
```python
db = SQLiteORM("productos.db")
db.conect_DB()

# 2. Insert

# Simple

db.insert(
    table_name="productos",
    items=[ "producto_x", 10.5, "2023-01-01", 1, 1]
)

# Massive

db.insert_many(
    table_name="productos",
    items=[
        ("producto_x", 10.5, "2023-01-01", 1, 1)
        for _ in range(5_000_000)
    ]
)

# 3. UPDATE

db.update(
    set_values={"nombre": "nuevo", "precio": 50},
    data=["id_producto", "IN", (1,2,3)],
    table_name="productos"
)

"""  Update all records with nombre and precio column"""
db.update(
    set_values={"nombre": "nuevo", "precio": 50},
    table_name="productos"
)

# OTHER UPDATE AND DELETE ALTERNATIVES 
# In case you want delete or update all records without necesity on seeting arguments, take those two functions
# ⚠️ Use delete_all() carefully. This operation removes every row from the table.

db.delete_all(table_name="productos")
db.update_all(set_values={"nombre": "nuevo", "precio": 50}, table_name="productos")

# 4. DELETE with and without conditions

db.delete(
    data=["precio", ">", 100],
    table_name="productos"
)

"""  Delete all records """
db.delete(
    table_name="productos"
)

# 5 

🧠 Architecture

SQLiteORM.py – Main engine

MySQLORM.py – MySQL adapter (in progress)

OracleORM.py – Oracle adapter (in progress)

builders/ – WHERE, SET, placeholders builders

stream/ – streaming operations

optimizers/ – pragma, vacuum, analyze

🧩 Roadmap

Full MySQL engine

Full Oracle engine

QueryBuilder

Model-based ORM layer

Automatic migrations

Batch UPDATE & DELETE

Foreign key inspector

PyPI release


👨‍💻 Author

Iván González Valles
[GitHub(https://github.com/ivanarganda)]
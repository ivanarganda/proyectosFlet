-- SQLite
CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL
            );

INSERT INTO roles (role)
    SELECT 'admin'
    WHERE NOT EXISTS (SELECT 1 FROM roles WHERE role = 'admin') 
    UNION
    SELECT 'user'
    WHERE NOT EXISTS (SELECT 1 FROM roles WHERE role = 'user')


CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                password TEXT NOT NULL,
                role INTEGER,
                FOREIGN KEY (role) REFERENCES roles(id) ON DELETE CASCADE
            );

INSERT INTO users (name, password)
    SELECT 'ivan', 'ivan1234'
    WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = 'ivan' and password = 'ivan1234') 
def get_queries():

    try:
        
        return { 
            "create_roles_table": """
                CREATE TABLE IF NOT EXISTS roles ( 
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    role TEXT NOT NULL
                )
            """,
            "init_roles_data": """
                INSERT OR IGNORE INTO roles (role)
                    SELECT 'admin'
                    WHERE NOT EXISTS (SELECT 1 FROM roles WHERE role = 'admin')
                    UNION
                    SELECT 'user'
                    WHERE NOT EXISTS (SELECT 1 FROM roles WHERE role = 'user')
            """,
            "create_users_table": """ 
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL, 
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    role INTEGER,
                    token TEXT,
                    FOREIGN KEY (role) REFERENCES roles(id) ON DELETE CASCADE
                )
            """,
            "init_user_admin_data": """
                INSERT INTO users (username, email, password, role)
                    SELECT ?, ?, ?, 1
                    WHERE NOT EXISTS (
                        SELECT 1 FROM users WHERE email = 'ivanartista96@gmail.com'
                    )
            """,
            "create_tasks_categories_table": """ 
                CREATE TABLE IF NOT EXISTS tasks_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL, 
                    content JSON NOT NULL,
                    id_user INTEGER,
                    FOREIGN KEY (id_user) REFERENCES users(id) ON DELETE CASCADE
                )
            """,
            "create_tasks_table": """ 
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content JSON NOT NULL, 
                    id_category INTEGER,
                    id_user INTEGER,
                    state INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (id_category) REFERENCES tasks_categories(id) ON DELETE CASCADE,
                    FOREIGN KEY (id_user) REFERENCES users(id) ON DELETE CASCADE
                )
            """
        }

    except ( KeyError, TypeError ):
        return False
def clear_screen():
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

def get_file_users():
    import os
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(BASE_DIR, "usuarios.txt")

def reiniciar_script():
    import os
    import sys
    os.execv(sys.executable, ['python'] + sys.argv)

def logout_user():
    import os
    SESSION_USER_FILE = generate_file_session_user()
    if os.path.exists(SESSION_USER_FILE):
        os.remove(SESSION_USER_FILE)
        print("Has cerrado sesión exitosamente.")
    else:
        print("No hay ninguna sesión activa.")
    return False

def generate_file_session_user():
    import os
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(BASE_DIR, "session_user.txt")

def check_session_user():
    import os
    SESSION_USER_FILE = generate_file_session_user()
    if os.path.exists(SESSION_USER_FILE):
        with open(SESSION_USER_FILE, "r") as f:
            content = f.read().strip()
            if content:
                return True
    return False

def get_session_user():
    import os
    SESSION_USER_FILE = generate_file_session_user()
    if os.path.exists(SESSION_USER_FILE):
        with open(SESSION_USER_FILE, "r") as f:
            content = f.read().strip()
            if content:
                return content.split(";")[0]
    return None

def generate_token_session():
    import uuid
    return str(uuid.uuid4())

def login():
    import time
    with open(get_file_users(), "r") as f:
        usuarios = f.readlines()
        while True:
            username = input("Usuario: ").strip()
            password = input("Contraseña: ").strip()
            for usuario in usuarios:
                user, pwd = usuario.strip().split(";")
                if user == username and pwd == password:
                    print(f"¡Bienvenido de nuevo, {username}!")
                    with open(get_session_user(), "w") as session_file:
                        session_file.write(f"{username};{generate_token_session()}")
                        # actualizar el menú principal
                        # esperar para que se inicie sesion
                        time.sleep(1)
                    return {
                        "logged":True,
                        "Message":f"Bienvenido {username}!!"
                    }
            return {
                "logged":False,
                "Message":"Usuario o contraseña incorrectos. Inténtalo de nuevo."
            }
    return {
        "logged":False,
        "Message":"Error inesperado en inicio de sesión."
    }

def generate_menu_items(menu_dict):
    return "\n".join([f"{k}. {v}" for k, v in menu_dict.items()])
def mostrar_menu_principal():
        
        return {
            "1": "Jugar como invitado" if not check_session_user() else "Continuar juego como " + get_session_user(),
            "2": "Jugar como usuario registrado" if not check_session_user() else "Cerrar sesión de " + get_session_user(),
            "3": "Salir"
        }

def mostrar_menu_login_registro():
    return {
        "1": "Iniciar sesión" if not check_session_user() else "Cerrar sesión",
        "2": "Registrarse" if not check_session_user() else "Cambiar de usuario",
        "3": "Volver al menú principal"
    }

def juego_niveles():

    return {
        "1": {
            "label": "Fácil",
            "intentos": 10,
            "min": 1,
            "max": 10,
            "handicap": True
        },
        "2": {
            "label": "Medio",
            "intentos": 8,
            "min": 1,
            "max": 20,
            "handicap": False
        },
        "3": {
            "label": "Difícil",
            "intentos": 4,
            "min": 1,
            "max": 30,
            "handicap": False
        }
    }

def mostrar_menu_niveles():
    # En un diccionario
    return {
        "1": "Fácil (1-10, 10 intentos, con pista)",
        "2": "Medio (1-20, 8 intentos, sin pista)",
        "3": "Difícil (1-30, 4 intentos, sin pista)",
        "4": "Volver al menú principal"
    }  
from utils import generate_menu_items, mostrar_menu_login_registro, clear_screen,get_file_users, generate_file_session_user, generate_token_session, check_session_user, logout_user
import time
# Generar token de sesion

USUARIOS_FILE = get_file_users()
SESSION_USER_FILE = generate_file_session_user()

def registrar_usuario():
    clear_screen()
    print("=== Registro de Usuario ===")
    # Aquí iría la lógica real de registro
    return False
        
def login_usuario():
    clear_screen()
    print("=== Inicio de Sesión ===")
    # Aquí iría la lógica real de login
    with open(USUARIOS_FILE, "r") as f:
        usuarios = f.readlines()
        while True:
            username = input("Usuario: ").strip()
            password = input("Contraseña: ").strip()
            for usuario in usuarios:
                user, pwd = usuario.strip().split(";")
                if user == username and pwd == password:
                    print(f"¡Bienvenido de nuevo, {username}!")
                    with open(SESSION_USER_FILE, "w") as session_file:
                        session_file.write(f"{username};{generate_token_session()}")
                        # actualizar el menú principal
                        # esperar para que se inicie sesion
                        time.sleep(1)
                    return True
            return False
    return False

def init_registro_login():
    # Comprobaremos antes si ya tiene la sesion iniciada y en caso de que si ya me lleva al juego
    while True:
                # Generamos el menú dinámico
        menu_login_registro = generate_menu_items(mostrar_menu_login_registro())

        # Guardamos las funciones directamente (no strings)
        dispatch_login_registro = {
            "1": login_usuario if not check_session_user() else logout_user,
            '2': registrar_usuario if not check_session_user() else logout_user,
        }
        try:
            print(menu_login_registro)
            opcion = input("\nSeleccione una opción: ").strip()

            if opcion.lower() == "3":  # salir rápido
                print("Saliendo del sistema de login/registro...")
                break

            if opcion in dispatch_login_registro:
                try:
                    dispatch_login_registro[opcion]()  # ejecuta la función
                except Exception as e:
                    print(f"⚠️ Error al ejecutar la opción: {e}")
            else:
                print("⚠️ Opción no válida. Intente nuevamente.\n")

        except KeyboardInterrupt:
            print("\n⚠️ Interrupción detectada. Saliendo...")
            break
        except Exception as e:
            print(f"⚠️ Ha ocurrido un error inesperado: {e}")

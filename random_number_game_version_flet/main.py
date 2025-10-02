from sys import exit
from game_room import init_game
from utils import mostrar_menu_principal, generate_menu_items , check_session_user, logout_user
from registro_login import init_registro_login

def main():
    while True:
        menu = generate_menu_items(mostrar_menu_principal())
        dispatch = {
            "1": lambda: init_game(),
            "2": lambda: init_registro_login() if not check_session_user() else logout_user(),
            "3": lambda: exit("👋 Adiós, hasta pronto!")
        }
        options = list(dispatch.keys())

        print("--- Juego de Adivina el Número ---")
        print(menu)

        choice = input(f"Selecciona una opción ({options[0]}-{options[-1]}): ")
        if choice in dispatch:
            dispatch[choice]()
        else:
            print("⚠️ Opción no válida, intenta de nuevo.")

if __name__ == "__main__":
    main()

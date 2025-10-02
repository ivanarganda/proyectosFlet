from utils import mostrar_menu_niveles, juego_niveles, generate_menu_items
import random

menu = generate_menu_items(mostrar_menu_niveles())

game_levels = juego_niveles()

def init_game():
    global game_levels
    key_options = list(game_levels.keys())
    while True:
        op = input(_menu_() + "\n> ")
        if not op.isdigit():
            continue
        op = int(op)
        if op < int(key_options[0]) or op > int(key_options[-1]) and op != 4:
            continue
        if op == 4:
            print("Adiós, hasta pronto!! :))")
            break
        start_game(game_levels.get(str(op)))
    
def start_game(level):
    min_ = level["min"]
    max_ = level["max"]
    intentos = level["intentos"]

    numero_secreto = random.randint(min_, max_)

    range_ = f"entre {min_} y {max_}" if level["handicap"] == True else ""

    print(f"\nNivel {level['label']}\nAdivina el número {range_} (tienes {intentos} intentos)\n")

    i = 0
    while i < intentos:
        intento = int(input(f"Te quedan {intentos-i} intentos\nEscribe un número {range_}: "))
        if level["handicap"] == True and (intento < min_ or intento > max_):
            print(f"Número fuera de rango ({min_} y {max_}), inténtalo de nuevo")
            continue
        if intento == numero_secreto:
            print(f"🎉 ¡Acertaste el número!")
            break
        elif intento < numero_secreto:
            print("El número es mayor")
            min_ = intento
        else:
            print("El número es menor")
            max_ = intento
        if level["handicap"] == True:
            range_ = f"entre {min_} y {max_}"
        i += 1
    else:
        print(f"❌ Perdiste, el número era {numero_secreto}")

def _menu_():
    opciones = menu
    return f"\nBienvenido al juego de adivinar número\nEscoge un nivel:\n{opciones}\n"
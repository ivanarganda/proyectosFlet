fruits = {}

common_options_menu = {
    "exit": "( or 'q' to exit 😓)",
    "confirm": "( 's' or 'n' 🤔)"
}

comon_success_messages = {
    "added": "Fruit added successfully!! 🎉",
    "deleted": "Fruit deleted successfully!! 🎉"
}

common_errors_exceptions = {
    "KeyboardInterrupt": f"❌ Error: Not keyboard interactivity allowed",
    "ValueError": f"❌ Error: data type"
}

def showFruits():
    global fruits
    if len(fruits) == 0: 
        return print("😓 You don´t have any fruit")
    for (start,fruit) in enumerate(fruits,start=1):
        print(f"{start}.{fruit} - ({fruits[fruit]})")

def addFruit():
    global fruits,common_options_menu,common_errors_exceptions
    print(f"\n==📖 Add a fruit {common_options_menu["exit"]}==\n")
    while True:
        try:
            showFruits()
            print("\n")
            new_fruit = input("Write a fruit you desire to add").strip()
            if new_fruit == "": raise Exception(f"Unable to add fruit as it must not be empty")
            if new_fruit in fruits: raise Exception(f"Already fruit {new_fruit} pending")
            quantity = int(input(f"Write a quantity for {new_fruit}").strip())
            fruits[new_fruit] = quantity
            showFruits()
            print(comon_success_messages["added"])
            while True:
                try:
                    confirm = input(f"🤔 Would you like to add new fruit? {common_options_menu["confirm"]}").strip()
                    if confirm == 's': break
                    if confirm == 'n': 
                        main_menu()
                        return
                except KeyboardInterrupt:
                    continue
                except ValueError:
                    continue
        except ValueError:
            print(common_errors_exceptions["ValueError"])
        except KeyboardInterrupt:
            print(common_errors_exceptions["KeyboardInterrupt"])
        except Exception as e:
            print(e)
    return

def deleteFruit():
    global fruits,common_options_menu,common_errors_exceptions
    print(f"\n==🗑️ Delete a fruit {common_options_menu["exit"]}\n")

    while True:
        try:
            showFruits()
            print("\n")
            op = input("Select option fruit yo desire to delete").strip()
            if op not in fruits: raise Exception(f"Unable to add fruit as it must not be empty")
            del fruits[op]
            showFruits()
            print(comon_success_messages["deleted"])
            while True:
                try:
                    confirm = input(f"🤔 Would you like to delete another fruit? {common_options_menu["confirm"]}").strip()
                    if confirm == 's': break
                    if confirm == 'n': 
                        main_menu()
                        return
                except KeyboardInterrupt:
                    continue
                except ValueError:
                    continue
        except ValueError:
            print(common_errors_exceptions["ValueError"])
        except KeyboardInterrupt:
            print(common_errors_exceptions["KeyboardInterrupt"])
        except Exception as e:
            print(e)
    return

dispatch = {
    "1":addFruit,
    "2":deleteFruit,
    "3":showFruits
}


def main_menu():
    global common_errors_exceptions
    while True:
        menu = "1.Add new fruit\n2.Delete a fruit\n3.Consult my fruits\n4.Leave\n"
        try:
            op = input(f"\n🎉==Welcome to the fruit warehouse menu==\n{menu}\nChoose one option\n").strip() 
            if op == "4":
                print("Catch you later! 👋")
                break
            if op not in dispatch: raise Exception("❌ Not allowed option")
            dispatch[str(op)]()
        except ValueError:
            print(common_errors_exceptions["ValueError"])
        except KeyboardInterrupt:
            print(common_errors_exceptions["KeyboardInterrupt"])
        except Exception as e:
            print(e)

if __name__ == "__main__":
    main_menu()
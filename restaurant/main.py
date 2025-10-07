import sys

# common functions
class NotFoundUser(Exception):pass
class NotFoundMenuOption(Exception):pass
class NotFoundMenu(Exception):pass
class NotFoundCredentials(Exception):pass
class ErrorLogin(Exception):pass
class NotMatchedLikes(Exception):pass

services = {
    "bad": lambda x: x < 30,
    "regular": lambda x: x >= 30 and x <= 50,
    "regular": lambda x: x > 50
}

common_options_menu = {
    "login_and_exit": "5.Log out\n6. exit" ,
    "exit": "( or 'q' to exit 😓)",
    "confirm": "( 's' or 'n' 🤔)"
}

common_success_messages = {
    "added": "Contact added successfully!! 🎉",
    "deleted": "Contact deleted successfully!! 🎉",
    "login": "Login successfully!! 🎉",
    "update": "Contact updated successfully!! 🎉"
}

common_errors_exceptions = {
    "KeyboardInterrupt": "❌ Error: Not keyboard interactivity allowed",
    "ValueError": "❌ Error: data type",
    "Not_found_user": "❌ Error: not found user",
    "Login": "❌ Error: credentials error",
    "Attemps_to_access": "❌ Error: Unable to access. Reached max allowed attempts",
    "Not_allowed_option": "❌ Error: Not allowed option",
    "Not_allowed_action": "❌ Error: Not allowed action",
    "found_contact": "❌ Error: Contact already exists",
    "Not_allowed_contact": "❌ Error: Not allowed contact",
    "Not_allowed_phone": "❌ Error: Not allowed phone",
    "Not_found_phone": "❌ Error: Not found phone"
}

list_users = ["joan","mikel","ivan"]

users = {
    "joan":{
        "role":"user",
        "password":"joan1234"
    },
    "mikel":{
        "role":"user",
        "password":"mikel1234"
    },
    "ivan":{
        "role":"admin",
        "password":"ivan1234"
    }
}

people_likes = {
    "restaurants":{},
    "ordered food": {},
    "method money save": {},
    "billing account": {}
}

restaurant = {
    "Goiko": {
        "ordered_menus": {},
        "billings":{},
        "menu": {
            1:{ 
                "dish":"cheese beakon hamburguer",
                "type": "food",
                "price":10
            },
            2:{ 
                "dish":"cheese beakon hamburguer",
                "type": "food",
                "price":13
            },
            3:{ 
                "dish":"cheese beakon hamburguer",
                "type": "food",
                "price":8
            },
            4:{ 
                "dish":"beer",
                "type": "drink",
                "price":3.75
            },
            5:{
                "dish":"orange fresh drink",
                "type": "drink",
                "price":4
            }
        },
        "sales": {
            1:{
              "title":"disccount beer after frinking more than one",
              "disccount": 2.50
            }
        },
        "reports": {}
    },
    "Montaditos": {
        "ordered_menus": {},
        "billings":{},
        "menu": {
            1:{ 
                "dish":"orange juice with toats of tomatoe or jam",
                "type": "brunch",
                "price":1.5
            },
            2:{ 
                "dish":"cesar salad",
                "type": "food",
                "price":2
            },
            3:{ 
                "dish":"jam and cheese buddy",
                "type": "food",
                "price":1
            },
            4:{ 
                "dish":"pops snack",
                "type": "food",
                "price":1
            },
            5:{ 
                "dish":"beer jar",
                "type": "drink",
                "price":2.50
            }
        },
        "sales": {
            1:{
              "title":"second beer jar",
              "disccount": 1
            }
        },
        "reports": {}
    }
}

def returnIndexUser(u):
    global list_users
    return list_users[u]

user = None
userLooged = False

def consult_restaurant(): pass
def add_restaurant(): pass
def delete_restaurant(): pass
def update_restaurant(): pass
def order_food(): pass
def delete_cart(): pass
def consult_current_cart(): pass
def redem_cupon(): pass

def Login():
    global user, users
    attempts = 0
    while True:
        try:
            username = input("Type username: ").strip()
            if username not in users:
                raise Exception(common_errors_exceptions["Not_found_user"])

            password = input("Type password: ").strip()
            if password != users[username]["password"]:
                attempts += 1
                if attempts >= 3:
                    raise Exception(common_errors_exceptions["Attemps_to_access"])
                else:
                    raise Exception(common_errors_exceptions["Login"])

            user = username
            role = users[username]["role"]
            userLogged = True
            print(common_success_messages["login"])
            main_menu()
            return
        except KeyboardInterrupt:
            print(common_errors_exceptions["KeyboardInterrupt"])
        except ValueError:
            print(common_errors_exceptions["ValueError"])
        except Exception as e:
            print(e)


main_menus = {
    "admin": {
        "menu": f"1.Add new restaurant\n2.Delete a restaurant\n3.Consult restaurant\n4.Update restaurant\n{common_options_menu["login_and_exit"]}",
        "dispatch": {
            "1":add_restaurant,
            "2":delete_restaurant,
            "3":consult_restaurant,
            "4":update_restaurant
        }
    },
    "user": {
        "menu": f"1.Order food\n2.Delete cart\n3.Consult my current cart\n4.Redem cupon\n{common_options_menu["login_and_exit"]}",
        "dispatch": {
            "1":order_food,
            "2":delete_cart,
            "3":consult_current_cart,
            "4":redem_cupon
        }
    }
}

def main_menu():
    while True:
        if userLogged == False: break
        menu = main_menus[role]["menu"]
        try:
            op = input(f"\n🎉==Welcome {user} ({role}) to the take away food menu==\n{menu}\nChoose one option: ").strip()
            if op == "5": 
                user = None
                role = None
                userLogged = False
            if op == "6":
                print("Catch you later! 👋")
                sys.exit(0)
            if op not in main_menus[role]["dispatch"]:
                raise NotFoundMenuOption(common_errors_exceptions["Not_allowed_option"])
            main_menus[role]["dispatch"][op]()
        except ErrorValue:
            print(common_errors_exceptions["Not_allowed_option"])
        except NotFoundMenuOption as e:
            print(e)

if __name__ == "__main__":
    if userLogged == True:
        main_menu()
    else:
        Login()
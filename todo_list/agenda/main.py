import sys
import re

# { contacto: { user: creador, phone: telefono } }
contacts = {}

regexes = {
    "phone": r"^\+?1?\d{9,15}$"
}

common_options_menu = {
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

users = {
    "ivan": {"role": "admin", "password": "ivan1234"},
    "mikel": {"role": "user", "password": "mikel1234"},
}

user = None
role = None
userLogged = False
attempts = 0


def Login():
    global user, role, userLogged, attempts
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


def showContacts():
    global contacts, user, role
    if len(contacts) == 0:
        print("😓 No contacts available")
        return

    print("\n=== 📒 Contact list ===")
    if role == "admin":
        for i, (name, data) in enumerate(contacts.items(), start=1):
            print(f"{i}. {name} - {data['phone']} (added by {data['user']})")
    else:
        found = False
        for i, (name, data) in enumerate(contacts.items(), start=1):
            if data['user'] == user:
                print(f"{i}. {name} - {data['phone']} (added by you)")
                found = True
        if not found:
            print("😓 You don’t have any contacts yet")


def addContact():
    global contacts
    print(f"\n==📖 Add a contact {common_options_menu['exit']}==\n")
    while True:
        try:
            new_contact = input("Write a contact you desire to add: ").strip()
            if new_contact == "":
                raise Exception(common_errors_exceptions["Not_allowed_contact"])
            if new_contact in contacts:
                raise Exception(common_errors_exceptions["found_contact"])

            phone = input(f"Write a phone number for {new_contact}: ").strip()
            if phone == "" or not re.fullmatch(regexes["phone"], phone):
                raise Exception(common_errors_exceptions["Not_allowed_phone"])

            contacts[new_contact] = {"user": user, "phone": phone}
            showContacts()
            print(common_success_messages["added"])

            confirm = input(f"🤔 Add another? {common_options_menu['confirm']} ").strip().lower()
            if confirm == 'n':
                return
        except Exception as e:
            print(e)
            return


def deleteContact():
    global contacts
    print(f"\n==🗑️ Delete a contact {common_options_menu['exit']}==\n")
    while True:
        try:
            showContacts()
            op = input("Select contact name to delete: ").strip()
            if op not in contacts:
                raise Exception("❌ Error: contact not found")

            if role != "admin" and contacts[op]["user"] != user:
                raise Exception("❌ Error: you can only delete your own contacts")

            del contacts[op]
            showContacts()
            print(common_success_messages["deleted"])

            confirm = input(f"🤔 Delete another? {common_options_menu['confirm']} ").strip().lower()
            if confirm == 'n':
                return
        except Exception as e:
            print(e)
            return


def updateContact():
    global contacts
    print(f"\n==✏️ Update a contact {common_options_menu['exit']}==\n")
    while True:
        try:
            showContacts()
            op = input("Select contact name to update: ").strip()
            if op not in contacts:
                raise Exception("❌ Error: contact not found")

            if role != "admin" and contacts[op]["user"] != user:
                raise Exception("❌ Error: you can only update your own contacts")

            new_phone = input(f"Enter new phone number for {op}: ").strip()
            if new_phone == "" or not re.fullmatch(regexes["phone"], new_phone):
                raise Exception(common_errors_exceptions["Not_allowed_phone"])

            contacts[op]["phone"] = new_phone
            showContacts()
            print(common_success_messages["update"])

            confirm = input(f"🤔 Update another? {common_options_menu['confirm']} ").strip().lower()
            if confirm == 'n':
                return
        except Exception as e:
            print(e)
            return


dispatch = {
    "1": addContact,
    "2": deleteContact,
    "3": showContacts,
    "4": updateContact
}


def main_menu():
    while True:
        menu = "1.Add new contact\n2.Delete a contact\n3.Consult my contacts\n4.Update a contact\n5.Leave\n"
        try:
            op = input(f"\n🎉==Welcome {user} ({role}) to the contact warehouse menu==\n{menu}\nChoose one option: ").strip()
            if op == "5":
                print("Catch you later! 👋")
                sys.exit(0)
            if op not in dispatch:
                raise Exception(common_errors_exceptions["Not_allowed_option"])
            dispatch[op]()
        except Exception as e:
            print(e)


if __name__ == "__main__":
    if userLogged:
        main_menu()
    else:
        Login()
my_tasks = [
    "do-washing up",
    "do laundry",
    "make a bed",
    "set the table"
]

common_options_menu = {
    "exit": "( or 'q' to exit 😓)",
    "confirm": "( 's' or 'n' 🤔)"
}

comon_success_messages = {
    "added": "Task added successfully!! 🎉",
    "deleted": "Task deleted successfully!! 🎉"
}

common_errors_exceptions = {
    "KeyboardInterrupt": f"❌ Error: Not keyboard interactivity allowed",
    "ValueError": f"❌ Error: data type"
}

def showTasks():
    global my_tasks
    if len(my_tasks) == 0: 
        return print("😓 You don´t have any tasks")
    for (start,task) in enumerate(my_tasks,start=1):
        print(f"{start}.{task}")

def addTask():
    global my_tasks,common_options_menu,common_errors_exceptions
    print(f"\n==📖 Add a task {common_options_menu["exit"]}==\n")
    while True:
        try:
            showTasks()
            print("\n")
            new_task = input("Write a task you desire to add").strip()
            if new_task == "": raise Exception(f"Unable to add task as it must not be empty")
            if new_task in my_tasks: raise Exception(f"Already task {new_task} pending")
            my_tasks.append(new_task)
            print(comon_success_messages["added"])
            while True:
                try:
                    confirm = input(f"🤔 Would you like to add new task? {common_options_menu["confirm"]}").strip()
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

def deleteTask():
    global my_tasks,common_options_menu,common_errors_exceptions
    print(f"\n==🗑️ Delete a task {common_options_menu["exit"]}\n")
    keys = positions = [i for i, x in enumerate(my_tasks)]
    while True:
        try:
            showTasks()
            print("\n")
            op = int(input("Select option task yo desire to delete").strip())
            if op not in keys: raise Exception(f"Unable to add task as it must not be empty")
            del my_tasks[op]
            print(comon_success_messages["deleted"])
            while True:
                try:
                    confirm = input(f"🤔 Would you like to delete another task? {common_options_menu["confirm"]}").strip()
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
    "1":addTask,
    "2":deleteTask,
    "3":showTasks
}


def main_menu():
    global common_errors_exceptions
    while True:
        menu = "1.Add new task\n2.Delete a task\n3.Consult my tasks\n4.Leave\n"
        try:
            op = input(f"\n🎉==Welcome to the task menu==\n{menu}\nChoose one option\n").strip() 
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
import os
import uuid
from typing import Dict
import requests
import cohere
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

import logging # TODO only for testing

logging.basicConfig(filename='process.log', level=logging.DEBUG)

# Load environment variables
load_dotenv()

# === GLOBALS ===
api_key = os.getenv("COHERE_API_KEY")
co = None
console = Console()

# === AUTHENTICATION ===
def get_client():
    """Create and store a Cohere client."""
    global co
    if not api_key:
        raise Exception("Missing COHERE_API_KEY in .env")
    co = cohere.ClientV2(api_key=api_key)
    return co


# === COMMAND TABLE ===
def show_table_commands():
    """Display available commands."""
    if co is None:
        raise Exception("Unable to send message — missing authentication")

    console.print(Panel.fit("[bold cyan]🧠 Cohere Chat CLI[/bold cyan]", border_style="bright_blue"))

    table = Table(title="[bold yellow]Available Commands[/bold yellow]", style="bold white")
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Description", style="green")

    table.add_row("new", "Start a new conversation")
    table.add_row("exit", "Exit the chat")

    console.print(table)


def show_all_conversations():
    pass


# === CHAT LOOP ===
def talk():
    """Main chat loop with Cohere."""
    if co is None:
        raise Exception("Unable to send message — missing authentication")

    conversation: Dict[str, Dict[str, str]] = {}

    console.print("[bold green]💬 Chat started. Type your message (or 'exit' to quit).[/bold green]\n")

    default_prompt = """ Eres un experto en análisis de datos.
                Te doy una muestra de unos DataFrames en JSON.
                fichero users.csv
                {
                    "users":[
                        {"id":1,"username":"ivan_arganda96"},
                        {"id":2,"username":"pablo_arganda"},
                        {"id":3,"username":"igvarg__"},
                        {"id":4,"username":"saraitg_654"},
                    ]
                }
                fechero tasks.xlsx 
                {
                    "tasks":[
                        {"id":1,"title":"go for a walk", id_user=1},
                        {"id":2,"title":"laundry", id_user=1},
                        {"id":3,"title":"housework", id_user=2},
                        {"id":4,"title":"go for classes", id_user=4},
                    ]
                }

                Tu tarea:
                1. Identifica el tipo de cada columna (numérico, texto, fecha, categoría, booleano, id, etc.)
                2. Detecta si alguna columna es clave primaria o clave externa.
                3. Agrupa columnas relacionadas lógicamente.
                4. Ya por último me pasas el codigo python pandas completo

                Devuelve un JSON con:
                {
                "columns": {
                    "col_name": {
                        "type": ...,
                        "role": ...,
                        "rename_suggestion": ...,
                        "notes": ...
                    }
                },
                "relationships": [...],
                "final_model": ...
                }
                """

    while True:
        message = input("\n[you]").strip() or default_prompt

        if message.lower() == "exit":
            console.print("[bold red]👋 Exiting chat...[/bold red]")
            break

        if message.lower() == "new":
            console.print("[yellow]🔄 Starting a new conversation...[/yellow]")
            conversation.clear()
            continue

        if not message:
            continue

        try:
            # Call Cohere Chat endpoint   
            res = co.chat_stream(  # What I send to agent
                model="command-a-03-2025",
                messages=[
                    {"role": "user", "content": message}
                ],
            )
            
            reply_cohere = ""
            for event in res:
                if event.type == "content-delta":
                    reply_cohere = f"{event.delta.message.content.text}"
                    print(reply_cohere, end="")

            reply = reply_cohere if reply_cohere else "No response" # What agent replies me

            # # Save conversation
            conv_id = str(uuid.uuid4())
            conversation[conv_id] = {"user": message, "agent": reply}

            # # Display agent response
            # console.print(f"[bold blue]Cohere:[/bold blue] {reply}\n")

        except requests.exceptions.RequestException as e:
            console.print(f"[bold red]API Error:[/bold red] {e}")
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")


# === MAIN ENTRY ===
def main():
    try:
        get_client()
        show_table_commands()
        console.print("[bold green]✅ Authenticated successfully![/bold green]\n")
        talk()
    except Exception as e:
        console.print(f"[bold red]❌ {e}[/bold red]")


if __name__ == "__main__":
    main()

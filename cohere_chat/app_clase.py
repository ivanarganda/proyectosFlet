import os
import uuid
from typing import Dict
import requests
import cohere
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel


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

def talk():
    """Main chat loop with Cohere."""
    if co is None:
        raise Exception("Unable to send message — missing authentication")

    conversation: Dict[str, Dict[str, str]] = {}

    console.print("[bold green]💬 Chat started. Type your message (or 'exit' to quit).[/bold green]\n")

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
            console.print(f"[bold blue]Cohere:[/bold blue] {reply}\n")

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
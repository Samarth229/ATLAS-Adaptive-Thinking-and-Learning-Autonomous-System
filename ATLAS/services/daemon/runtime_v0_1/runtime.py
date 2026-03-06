import time
from rich.console import Console

console = Console()

def start_runtime():
    console.print("[bold yellow]A.T.L.A.S entering development runtime loop...[/bold yellow]")
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        console.print("\n[bold red]Shutdown signal received.[/bold red]")
        console.print("[bold cyan]A.T.L.A.S shutting down safely.[/bold cyan]")
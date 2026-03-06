import time
from rich.console import Console
from .event_bus import EventBus

console = Console()

def start_runtime():
    console.print("[bold yellow]A.T.L.A.S entering event-driven runtime (v0.2)...[/bold yellow]")

    event_bus = EventBus()

    event_bus.publish("system_started")

    try:
        while True:
            event = event_bus.get_event()

            if event:
                handle_event(event, event_bus)

            time.sleep(0.5)

    except KeyboardInterrupt:
        console.print("\n[bold red]Shutdown signal received.[/bold red]")
        console.print("[bold cyan]A.T.L.A.S shutting down safely.[/bold cyan]")

def handle_event(event, event_bus):
    event_type = event["type"]

    if event_type == "system_started":
        console.print("[green]Event:[/green] system_started")
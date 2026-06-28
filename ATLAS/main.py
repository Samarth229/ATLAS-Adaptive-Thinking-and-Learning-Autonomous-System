import sys
from atlas_core.boot.initializer import initialize_system


def main():
    system_context = initialize_system()
    mode = sys.argv[1] if len(sys.argv) > 1 else "text"

    if mode == "voice":
        import signal
        from rich.console import Console
        from interface.voice.voice_runtime import VoiceRuntime
        runtime = VoiceRuntime(system_context)
        def _shutdown(sig, frame):
            runtime._wakeword.stop()
            Console().print("\n[bold red]Voice runtime shut down.[/bold red]")
            raise SystemExit(0)
        signal.signal(signal.SIGINT, _shutdown)
        runtime.start()
    elif mode == "gui":
        from interface.gui.flask_server import run_server
        run_server()
    else:
        from services.daemon.runtime_v0_5.runtime import start_runtime
        start_runtime(system_context["identity"])


if __name__ == "__main__":
    main()
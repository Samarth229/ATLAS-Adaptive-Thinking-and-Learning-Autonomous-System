from atlas_core.boot.initializer import initialize_system
from services.daemon.runtime_v0_5.runtime import start_runtime

def main():
    system_context = initialize_system()
    start_runtime(system_context["identity"])

if __name__ == "__main__":
    main()
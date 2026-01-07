# Scripts/main.py
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent

def find_tools(root: Path):
    """Scannt alle Unterordner nach .py-Skripten (außer __init__.py, main.py und utils)."""
    tools = {}
    for py_file in root.rglob("*.py"):
        if py_file.name in ("__init__.py", "main.py"):
            continue
        if "utils" in py_file.parts:  # Dateien in utils/ ignorieren
            continue
        # Name für Menü: Ordnername + Dateiname ohne .py
        rel_path = py_file.relative_to(root)
        menu_name = f"{rel_path.parent}/{py_file.stem}" if rel_path.parent != Path(".") else py_file.stem
        tools[menu_name] = rel_path
    return dict(sorted(tools.items()))


TOOLS = find_tools(ROOT)

def run_tool(choice: str):
    # Pfad in Modulname konvertieren: pdf_tools/image_to_pdf.py -> pdf_tools.image_to_pdf
    rel_path = TOOLS[choice].with_suffix('')  # .py entfernen
    module_name = str(rel_path).replace('/', '.').replace('\\', '.')
    subprocess.run([sys.executable, "-m", module_name], check=False)

def main():
    print("\nVerfügbare Tools:")
    for i, name in enumerate(TOOLS, start=1):
        print(f"{i}. {name}")

    try:
        choice = int(input("\nNummer wählen: "))
        if 1 <= choice <= len(TOOLS):
            run_tool(list(TOOLS.keys())[choice - 1])
        else:
            print("Ungültige Auswahl.")
    except ValueError:
        print("Bitte eine Zahl eingeben.")

if __name__ == "__main__":
    main()

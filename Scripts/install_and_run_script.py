import subprocess
import sys
import os
import ast
import importlib.util
import platform
from pathlib import Path

# --- KONFIGURATION & DATEN ---

ROOT = Path(__file__).parent

# Mapping: Import-Name -> Pip-Paket-Name
PACKAGE_MAPPING = {
    "PIL": "Pillow",
    "sklearn": "scikit-learn",
    "yaml": "PyYAML",
    "cv2": "opencv-python",
    "bs4": "beautifulsoup4",
    "docx": "python-docx",
    "fitz": "pymupdf",
    "dotenv": "python-dotenv",
    "wx": "wxPython",
    "win32com": "pywin32",
    "win32api": "pywin32",
    "win32gui": "pywin32",
    "serial": "pyserial",
    "usb_monitor": "usb_monitor",
    "tkdnd": "tkinterdnd2" 
}

# Standard-Lib (werden ignoriert)
STD_LIB = {
    "sys", "os", "subprocess", "pathlib", "typing", "argparse", "re", 
    "math", "platform", "time", "shutil", "enum", "datetime", "json",
    "random", "collections", "functools", "itertools", "io", "csv",
    "tkinter", "logging", "threading", "multiprocessing", "ast", "contextlib",
    "socket", "inspect", "traceback", "signal", "unittest", "tempfile",
    "email", "string", "shlex", "mimetypes", "dataclasses", "zipfile", 
    "webbrowser", "ctypes", "hashlib", "faulthandler", "ssl", "fractions", 
    "smtplib", "concurrent", "copy", "warnings", "weakref", "site", "errno",
    "winreg", "distutils", "calendar", "uuid", "abc", "xml", "http", "urllib"
}

class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# --- DEPENDENCY SCANNER LOGIK ---

def get_imports_from_file(filepath: Path) -> set:
    """Parst eine Python-Datei und gibt alle importierten Modulnamen zurück."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            tree = ast.parse(f.read())
    except Exception:
        return set()

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])
    return imports

def resolve_local_path(root: Path, import_name: str) -> Path:
    """
    Versucht herauszufinden, ob ein Import lokal existiert.
    Z.B. import_name='utils.pdf' -> sucht nach 'root/utils/pdf.py'
    """
    # 1. Ersetze Punkte durch Pfadtrenner (utils.pdf -> utils/pdf)
    rel_path = import_name.replace('.', os.sep)
    
    # Check 1: Ist es eine .py Datei? (utils/pdf.py)
    candidate_py = root / (rel_path + ".py")
    if candidate_py.exists():
        return candidate_py
    
    # Check 2: Ist es ein Package? (utils/pdf/__init__.py)
    candidate_init = root / rel_path / "__init__.py"
    if candidate_init.exists():
        return candidate_init
    
    return None

def scan_dependencies_recursive(start_file: Path):
    """
    Scannt rekursiv ab der Startdatei. Folgt lokalen Importen.
    Gibt ein Set aller EXTERNEN Pakete zurück, die benötigt werden.
    """
    needed_externals = set()
    visited_files = set()
    queue = [start_file]

    visited_files.add(start_file)

    while queue:
        current_file = queue.pop(0)
        
        # Hole Imports aus dieser Datei
        raw_imports = get_imports_from_file(current_file)
        
        for imp in raw_imports:
            if imp in STD_LIB:
                continue
            
            # Prüfen: Ist das ein lokaler Import?
            local_path = resolve_local_path(ROOT, imp)
            
            if local_path:
                # Ja -> Zur Queue hinzufügen, falls noch nicht gescannt
                if local_path not in visited_files:
                    visited_files.add(local_path)
                    queue.append(local_path)
            else:
                # Nein -> Es ist wahrscheinlich extern (oder Standard-Lib die wir vergessen haben)
                needed_externals.add(imp)
                
    return needed_externals

def ensure_dependencies(target_file: Path):
    """
    Hauptfunktion: Prüft Dependencies für EINE Datei, fragt User, installiert.
    """
    print(f"{Colors.BLUE} Prüfe Abhängigkeiten für {target_file.name}...{Colors.RESET}", end="\r")
    
    # 1. Rekursiver Scan
    required_imports = scan_dependencies_recursive(target_file)
    
    # 2. Prüfen was installiert werden muss
    missing_packages = set()
    
    for imp in required_imports:
        # Mapping anwenden (cv2 -> opencv-python)
        install_name = PACKAGE_MAPPING.get(imp, imp)
        
        # Prüfen ob installed (Check auf Import-Namen!)
        if importlib.util.find_spec(imp) is None:
             # Zweiter Check: Manchmal heißt das Spec anders als der Import
            if importlib.util.find_spec(install_name) is None:
                missing_packages.add(install_name)

    if not missing_packages:
        print(f"{Colors.GREEN} Alle Abhängigkeiten OK.                                 {Colors.RESET}")
        return True

    # 3. User Interaktion
    print(f"\n{Colors.RED} Fehlende Pakete für dieses Tool detected:{Colors.RESET}")
    for pkg in missing_packages:
        print(f"  - {pkg}")
    
    try:
        choice = input(f"\n{Colors.BLUE}Jetzt installieren? (y/n): {Colors.RESET}").lower()
        if choice == 'y':
            print("Installiere...", end=" ")
            for pkg in missing_packages:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
            print(f"{Colors.GREEN}Fertig!{Colors.RESET}\n")
            return True
        else:
            print("Abbruch.")
            return False
    except Exception as e:
        print(f"Fehler bei Installation: {e}")
        return False

# --- MAIN MENU LOGIK ---

def find_tools(root: Path):
    """Scannt alle Unterordner nach .py-Skripten (außer __init__.py, main.py und utils)."""
    tools = {}
    for py_file in root.rglob("*.py"):
        if py_file.name in ("__init__.py", "main.py", "setup_dependencies.py"):
            continue
        # Ignoriere utils Ordner und venv/node_modules
        if any(x in py_file.parts for x in ["utils", "venv", "node_modules", "__pycache__"]):
            continue
            
        rel_path = py_file.relative_to(root)
        menu_name = f"{rel_path.parent}/{py_file.stem}" if rel_path.parent != Path(".") else py_file.stem
        # Schöner formatieren (Backslashes weg)
        menu_name = menu_name.replace('\\', '/')
        tools[menu_name] = rel_path
        
    return dict(sorted(tools.items()))

TOOLS = find_tools(ROOT)

def run_tool(choice: str):
    file_path = ROOT / TOOLS[choice]
    
    # --> CHECK DEPENDENCIES BEFORE RUNNING <--
    if not ensure_dependencies(file_path):
        return

    # Pfad in Modulname konvertieren
    rel_path = TOOLS[choice].with_suffix('')
    module_name = str(rel_path).replace('/', '.').replace('\\', '.')
    
    print(f"{Colors.GREEN}>>> Starte {module_name}...{Colors.RESET}\n")
    try:
        subprocess.run([sys.executable, "-m", module_name], check=False)
    except KeyboardInterrupt:
        print("\nBeendet.")

def main():
    # ANSI Farben unter Windows aktivieren
    if platform.system() == "Windows":
        os.system('color')

    while True:
        print("\n" + "="*30)
        print("    SCRIPT LAUNCHER")
        print("="*30)
        
        tool_list = list(TOOLS.keys())
        for i, name in enumerate(tool_list, start=1):
            print(f"{i}. {name}")
        print("0. Beenden")

        try:
            inp = input("\nNummer wählen: ")
            if inp == "0":
                break
            
            choice = int(inp)
            if 1 <= choice <= len(tool_list):
                selected_tool_name = tool_list[choice - 1]
                run_tool(selected_tool_name)
            else:
                print(f"{Colors.RED}Ungültige Auswahl.{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}Bitte eine Zahl eingeben.{Colors.RESET}")
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
import ast
import os
import sys
import subprocess
import importlib.util
import platform

# --- KONFIGURATION ---

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# Ordner, die NICHT gescannt werden sollen (npm, builds, venvs, git)
IGNORE_DIRS = {
    "node_modules", "dist", "build", "target",
    "venv", "env", ".git", ".idea", ".vscode",
    "__pycache__", "site-packages", "Lib", "Scripts", "bin", "obj"
}

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

# --- HELPER FUNKTIONEN ---

def enable_colors():
    if platform.system() == "Windows":
        os.system('color')

def get_all_local_modules(root_dir):
    """Scannt REKURSIV alle Dateien im Projekt (ignoriert node_modules)."""
    local_mods = set()
    print(f"{Colors.BLUE}--- Indiziere lokale Projekt-Dateien... ---{Colors.RESET}")
    
    for root, dirs, files in os.walk(root_dir):
        # Filter: Alles was in IGNORE_DIRS ist oder mit '.' beginnt, fliegt raus
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in IGNORE_DIRS]
        
        for file in files:
            if file.endswith(".py"):
                local_mods.add(file[:-3])
        
        for d in dirs:
            local_mods.add(d)

    print(f"Lokal erkannt: {len(local_mods)} Module (werden nicht installiert).\n")
    return local_mods

def get_imports_from_file(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        try:
            tree = ast.parse(f.read())
        except:
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

def check_installation(import_name):
    # 1. Import-Name prüfen (z.B. 'cv2')
    spec = importlib.util.find_spec(import_name)
    # 2. Install-Name holen
    install_name = PACKAGE_MAPPING.get(import_name, import_name)
    return spec is not None, install_name

def main():
    enable_colors()
    importlib.invalidate_caches()
    
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Lokale Dateien finden
    local_modules = get_all_local_modules(root_dir)

    # 2. Imports scannen
    print(f"{Colors.BLUE}--- Scanne Imports in Python-Dateien... ---{Colors.RESET}")
    all_imports = set()
    
    for root, dirs, files in os.walk(root_dir):
        # Filter anwenden
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in IGNORE_DIRS]
        
        for file in files:
            if file.endswith(".py") and file != os.path.basename(__file__):
                full_path = os.path.join(root, file)
                # Nur scannen, wenn nicht in node_modules (doppelter Boden)
                if "node_modules" in full_path: continue
                
                all_imports.update(get_imports_from_file(full_path))

    # 3. Auswertung
    installed_packages = set()
    missing_packages = set()

    for imp in sorted(all_imports):
        if imp in STD_LIB: continue
        if imp in local_modules: continue

        is_inst, install_name = check_installation(imp)
        
        if is_inst:
            installed_packages.add(install_name)
        else:
            missing_packages.add(install_name)

    # Bereinigung: Aliases entfernen
    missing_packages = missing_packages - installed_packages

    print(f"\n{Colors.HEADER}=== STATUS BERICHT ==={Colors.RESET}")
    
    if installed_packages:
        print(f"\n{Colors.BOLD}Bereits installiert ({len(installed_packages)}):{Colors.RESET}")
        print(f"{Colors.GREEN}" + ", ".join(sorted(list(installed_packages))) + f"{Colors.RESET}")

    if not missing_packages:
        print(f"\n{Colors.GREEN}{Colors.BOLD}Alles perfekt! Keine fehlenden Pakete.{Colors.RESET}")
        return

    unique_missing = sorted(list(missing_packages))
    
    print(f"\n{Colors.RED}{Colors.BOLD}FEHLENDE PAKETE ({len(unique_missing)}):{Colors.RESET}")
    for pkg in unique_missing:
        print(f"  [ ] {pkg}")

    print("-" * 40)
    
    try:
        choice = input(f"{Colors.BLUE}Sollen diese {len(unique_missing)} Pakete jetzt installiert werden? (y/n): {Colors.RESET}").lower()
    except KeyboardInterrupt:
        return

    if choice == 'y':
        print("\n--- Starte Installation ---")
        for pkg in unique_missing:
            print(f"Installiere {pkg}...", end=" ")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg], stdout=subprocess.DEVNULL)
                print(f"{Colors.GREEN}[OK]{Colors.RESET}")
            except subprocess.CalledProcessError:
                print(f"{Colors.RED}[FEHLER]{Colors.RESET}")
        print(f"\n{Colors.GREEN}Fertig.{Colors.RESET}")
    else:
        print("Abbruch.")

if __name__ == "__main__":
    main()
import os
import shutil
import subprocess
import tempfile
from PIL import Image
import importlib.util

# --- Defines ---
PATH_FOR_ICONS = r"D:\Scripts\Mathias\_Icons"
PATH_FOR_EXE = r"D:\Scripts\Mathias\_EXE"

# --- Inputs ---
python_file = input("Enter path to Python file (.py): ").strip().strip('"')
icon_file = input("Enter path to icon file (.ico or .png): ").strip().strip('"')
name_exe = input("Enter Name (without .exe): ").strip()

# --- Validate inputs ---
if not os.path.isfile(python_file):
    print("Error: Python file does not exist.")
    exit(1)
if not os.path.isfile(icon_file):
    print("Error: Icon file does not exist.")
    exit(1)

# --- Ask if GUI or CMD ---
build_type = input("Build as GUI or CMD? (g/c): ").strip().lower()
if build_type == "g":
    windowed_flag = "--windowed"
elif build_type == "c":
    windowed_flag = "--console"
else:
    print("Invalid choice. Defaulting to GUI.")
    windowed_flag = "--windowed"
    
# --- PNG to ICO if needed ---
ext = os.path.splitext(icon_file)[1].lower()
os.makedirs(PATH_FOR_ICONS, exist_ok=True)
os.makedirs(PATH_FOR_EXE, exist_ok=True)
file_name = os.path.basename(icon_file)

if ext == ".png":
    # Convert PNG to ICO
    ico_file_name = os.path.splitext(file_name)[0] + ".ico"
    icon_file_converted = os.path.join(PATH_FOR_ICONS, ico_file_name)
    
    img = Image.open(icon_file)
    img.save(icon_file_converted, format="ICO")
    
    icon_file = icon_file_converted

elif ext == ".ico":
    dest_icon = os.path.join(PATH_FOR_ICONS, file_name)
    
    # Skip copying if already in PATH_FOR_ICONS
    if os.path.abspath(icon_file) != os.path.abspath(dest_icon):
        if os.path.exists(dest_icon):
            try:
                os.remove(dest_icon)  # Overwrite if exists
            except PermissionError:
                print(f"Cannot overwrite {dest_icon}, it is in use.")
                exit(1)
        shutil.copy2(icon_file, dest_icon)
    
    icon_file = dest_icon

else:
    print("Error: Icon must be .png or .ico")
    exit(1)

# --- Detect Qt binding actually used ---
def detect_qt_binding(file_path):
    """Return 'PyQt5', 'PySide6', or None based on imports in the script."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    if "PyQt5" in content:
        return "PyQt5"
    elif "PySide6" in content:
        return "PySide6"
    return None

used_binding = detect_qt_binding(python_file)
exclude_modules = []

# Determine which Qt binding to exclude
if importlib.util.find_spec("PyQt5") and importlib.util.find_spec("PySide6"):
    if used_binding == "PyQt5":
        exclude_modules.append("PySide6")
        print("Both PyQt5 and PySide6 detected. Excluding PySide6 (script uses PyQt5).")
    elif used_binding == "PySide6":
        exclude_modules.append("PyQt5")
        print("Both PyQt5 and PySide6 detected. Excluding PyQt5 (script uses PySide6).")
    else:
        exclude_modules.append("PySide6")
        print("Both Qt bindings detected but script does not explicitly import either. Excluding PySide6 by default.")
elif importlib.util.find_spec("PyQt5"):
    exclude_modules.append("PySide6")
elif importlib.util.find_spec("PySide6"):
    exclude_modules.append("PyQt5")

exclude_args = [f"--exclude-module={mod}" for mod in exclude_modules]

# --- Paths ---
tmp_dir = os.path.join(tempfile.gettempdir(), "PythonToExe")
os.makedirs(tmp_dir, exist_ok=True)
py_filename = os.path.basename(python_file)

# --- Step 1: Copy Python file to temp folder ---
shutil.copy2(python_file, tmp_dir)

# --- Step 2: Run PyInstaller ---
os.chdir(tmp_dir)
cmd = [
    "pyinstaller",
    "--onefile",
    windowed_flag,  
    f"--icon={icon_file}",
] + exclude_args + [py_filename]

print("Running PyInstaller...")
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print("PyInstaller failed:")
    print(result.stdout)
    print(result.stderr)
    exit(1)

# --- Step 3: Copy .exe back to original folder ---
dist_exe = os.path.join(tmp_dir, "dist", os.path.splitext(py_filename)[0] + ".exe")
output_path = os.path.join(PATH_FOR_EXE, name_exe + ".exe")

if os.path.isfile(dist_exe):
    shutil.copy2(dist_exe, output_path)
    print(f"Executable created: {output_path}")
else:
    print("Error: .exe not found after PyInstaller run.")

# --- Step 4: Safe cleanup temp folder ---
def safe_rmtree(path):
    """Remove a directory and ignore files in use (Windows)."""
    if os.path.exists(path):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                try:
                    os.remove(os.path.join(root, name))
                except Exception:
                    pass
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                except Exception:
                    pass
        try:
            os.rmdir(path)
        except Exception:
            pass

safe_rmtree(tmp_dir)
print("Temporary files cleaned up.")
print() # enpty line for visibility
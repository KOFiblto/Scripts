import os
import sys
from win32com.client import Dispatch

def get_startup_folder():
    return os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup")

def set_autostart(enable=True):
    startup_folder = get_startup_folder()
    shortcut_path = os.path.join(startup_folder, "AutoBackup.lnk")
    
    if enable:
        # If running as a script, we want to launch pythonw.exe with the script
        # If frozen (exe), we launch the exe.
        
        if getattr(sys, 'frozen', False):
            target = sys.executable
            arguments = ""
            work_dir = os.path.dirname(sys.executable)
        else:
            # Running as script
            # Use pythonw.exe to avoid console window
            target = sys.executable.replace("python.exe", "pythonw.exe")
            # Current script path. Assuming this function is called from main.py or similar context
            # We need the absolute path to main.py. 
            script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
            arguments = f'"{script_path}"'
            work_dir = os.path.dirname(script_path)

        try:
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target
            shortcut.Arguments = arguments
            shortcut.WorkingDirectory = work_dir
            shortcut.Description = "AutoBackup Background Service"
            shortcut.save()
            return True
        except Exception as e:
            print(f"Failed to create shortcut: {e}")
            return False
        
    else:
        if os.path.exists(shortcut_path):
            try:
                os.remove(shortcut_path)
                return True
            except Exception as e:
                print(f"Failed to remove shortcut: {e}")
                return False
        return True

def is_autostart_enabled():
    startup_folder = get_startup_folder()
    shortcut_path = os.path.join(startup_folder, "AutoBackup.lnk")
    return os.path.exists(shortcut_path)

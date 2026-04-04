import subprocess
import os
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_vc_path():
    vc_paths = [
        r"C:\Program Files\VeraCrypt\VeraCrypt.exe",
        r"C:\Program Files (x86)\VeraCrypt\VeraCrypt.exe"
    ]
    for p in vc_paths:
        if os.path.exists(p):
            return p
    return None

def is_mounted(safe):
    path = safe.get('path', '')
    if not os.path.exists(path):
        return False

    if safe.get('type') == "VHDX":
        ps_check = f"(Get-DiskImage -ImagePath '{path}').Attached"
        result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_check], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return "True" in result.stdout
    elif safe.get('type') == "VeraCrypt":
        try:
            # VeraCrypt typically locks the container write access while mounted
            with open(path, 'a'):
                pass
            return False
        except IOError:
            return True
    return False

def dismount_safe(safe):
    if safe['type'] == "VHDX":
        if not is_admin():
            raise PermissionError("Administrator privileges are required to dismount VHDX files.")
        subprocess.run(["powershell", "-NoProfile", "-Command", f"Dismount-DiskImage -ImagePath '{safe['path']}'"], creationflags=subprocess.CREATE_NO_WINDOW)
    elif safe['type'] == "VeraCrypt":
        vc_path = get_vc_path()
        if not vc_path:
            raise FileNotFoundError("VeraCrypt executable not found.")
        
        letter = safe.get('preferred_letter')
        if letter:
            subprocess.run([vc_path, '/d', letter, '/q', '/s'], creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            subprocess.Popen([vc_path, '/d'])

def dismount_all():
    import database
    safes = database.load_safes()
    for s in safes:
        if s['type'] == "VHDX" and is_mounted(s):
            try:
                subprocess.run(["powershell", "-NoProfile", "-Command", f"Dismount-DiskImage -ImagePath '{s['path']}'"], creationflags=subprocess.CREATE_NO_WINDOW)
            except:
                pass
    
    vc_path = get_vc_path()
    if vc_path:
        subprocess.run([vc_path, '/d', '/q', '/s'], creationflags=subprocess.CREATE_NO_WINDOW)

def mount_veracrypt(path, drive_letter):
    vc_path = get_vc_path()
    if not vc_path:
        raise FileNotFoundError("VeraCrypt executable not found in standard paths.")

    cmd = [vc_path, '/v', path, '/l', drive_letter, '/explore', '/q', 'background']
    try:
        subprocess.Popen(cmd)
    except Exception as e:
        raise Exception(f"Failed to execute VeraCrypt: {e}")

def mount_vhdx(path, password, drive_letter):
    if not is_admin():
        raise PermissionError("Administrator privileges are required to mount and unlock VHDX files.")

    ps_mount = f'$img = Mount-DiskImage -ImagePath "{path}" -PassThru; $img | Get-Disk | Get-Partition | Get-Volume | Select-Object -ExpandProperty DriveLetter'
    
    result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_mount], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
    
    temp_letter = result.stdout.strip()
    
    if result.returncode != 0 and "already mounted" not in result.stderr.lower():
        if not temp_letter:
            raise Exception(f"Failed to mount VHDX: {result.stderr.strip()}")

    if not temp_letter:
        raise Exception("Failed to retrieve temporary drive letter mapping.")
        
    target_vol = f"{temp_letter}:"
    
    bde_cmd = ["manage-bde", "-unlock", target_vol, "-Password"]
    bde_proc = subprocess.run(bde_cmd, input=password, text=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    
    if bde_proc.returncode != 0:
        subprocess.run(["powershell", "-NoProfile", "-Command", f'Dismount-DiskImage -ImagePath "{path}"'], creationflags=subprocess.CREATE_NO_WINDOW)
        raise Exception("Failed to unlock VHDX. Invalid password or BitLocker error.")
        
    if temp_letter.upper() != drive_letter.upper():
        ps_change = f'Set-Partition -DriveLetter {temp_letter} -NewDriveLetter {drive_letter}'
        change_proc = subprocess.run(["powershell", "-NoProfile", "-Command", ps_change], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        if change_proc.returncode != 0:
            raise Exception(f"Drive unlocked, but failed to assign letter {drive_letter}.")

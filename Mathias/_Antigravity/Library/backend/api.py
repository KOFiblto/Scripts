import os
import platform
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class FileItem(BaseModel):
    name: str
    path: str
    type: str  # 'file' or 'directory'
    mime_type: Optional[str] = None

def get_drives():
    drives = []
    if platform.system() == "Windows":
        import string
        from ctypes import windll
        drives = []
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drives.append(f"{letter}:\\")
            bitmask >>= 1
    else:
        drives.append("/")
    return drives

@router.get("/libraries")
async def list_libraries():
    """List available drives or root paths."""
    return {"drives": get_drives()}

@router.post("/scan")
async def scan_directory(path: str):
    """List contents of a directory."""
    p = Path(path)
    if not p.exists() or not p.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")

    items = []
    try:
        # Scan directory
        for entry in os.scandir(p):
            try:
                is_dir = entry.is_dir()
                mime_type = None
                if not is_dir:
                    # Simple mime type guess based on extension
                    ext = entry.name.lower().split('.')[-1] if '.' in entry.name else ''
                    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
                        mime_type = 'image/' + ext
                    elif ext in ['mp4', 'webm', 'mkv', 'avi', 'mov']:
                        mime_type = 'video/' + ext
                    else:
                        continue # Skip non-media files for now? Or show all? 
                        # User said "look around its folders", so maybe show folders and media.
                
                if is_dir or mime_type:
                    items.append(FileItem(
                        name=entry.name,
                        path=entry.path,
                        type='directory' if is_dir else 'file',
                        mime_type=mime_type
                    ))
            except PermissionError:
                continue
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    # Sort: directories first, then files
    items.sort(key=lambda x: (x.type != 'directory', x.name.lower()))
    return {"items": items, "current_path": str(p)}

import subprocess
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import pyperclip
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)  # SYSTEM_DPI_AWARE
except Exception:
    pass

if len(sys.argv) > 1:
    filepath = sys.argv[1]
else:
    filepath = None

SUPPORTED_CODECS = ['aac', 'ac3', 'eac3']
UNSUPPORTED_CODECS = ['truehd']

def get_audio_codecs(filepath):
    result = subprocess.run([
        'ffprobe', '-v', 'error',
        '-select_streams', 'a',
        '-show_entries', 'stream=codec_name',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        filepath
    ], capture_output=True, text=True)
    return list(set(result.stdout.strip().splitlines()))

def convert_to_ac3(filepath):
    folder, filename = os.path.split(filepath)
    name, ext = os.path.splitext(filename)
    new_name = f"{name} + AC3{ext}"
    output_path = os.path.join(folder, new_name)

    cmd = [
        'ffmpeg', '-i', filepath,
        '-map', '0',
        '-c:v', 'copy',
        '-c:a', 'ac3',
        '-b:a', '640k',
        '-c:s', 'copy',
        output_path
    ]

    subprocess.run(cmd)
    messagebox.showinfo("Fertig", f"Konvertiert: {output_path}")

def update_codec_display(codecs, filepath):
    codec_display.config(state='normal')
    codec_display.delete('1.0', tk.END)

    if not codecs:
        codec_display.insert(tk.END, "Keine Audio-Codecs gefunden\n", 'orange')
        codec_display.config(state='disabled')
        return

    for codec in codecs:
        if codec in SUPPORTED_CODECS:
            color = 'green'
            status = 'unterstützt'
        elif codec in UNSUPPORTED_CODECS:
            color = 'red'
            status = 'nicht unterstützt'
        else:
            color = 'orange'
            status = 'unbekannt'
        codec_display.insert(tk.END, f"{codec} ({status})\n", color)
    codec_display.config(state='disabled')

    for codec in codecs:
        if codec in SUPPORTED_CODECS:
            return
    if messagebox.askyesno("Frage", f"In AC3 umwandeln?\n\n{os.path.basename(filepath)}"):
        convert_to_ac3(filepath)

def handle_file(path):
    path = path.strip('{}')  # Handles Windows drag format
    if not os.path.isfile(path):
        messagebox.showerror("Fehler", "Datei nicht gefunden.")
        return
    entry.delete(0, tk.END)
    entry.insert(0, path)
    codecs = get_audio_codecs(path)
    update_codec_display(codecs, path)

def browse_file():
    file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mkv *.mp4 *.mov")])
    if file_path:
        handle_file(file_path)

def paste_clipboard():
    clip = pyperclip.paste()
    if clip:
        if clip.startswith('"') and clip.endswith('"'):
            clip = clip[1:-1]
        handle_file(clip)

def on_drop(event):
    handle_file(event.data)

# --- GUI SETUP ---
try:
    import tkinterdnd2 as tkdnd
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "tkinterdnd2"])
    import tkinterdnd2 as tkdnd

root = tkdnd.TkinterDnD.Tk()
root.title("🎬 AC3 Audio-Konverter")
root.configure(bg="#1e1e1e")
root.geometry("900x600")

font_style = ("Segoe UI", 10)
btn_style = {"font": font_style, "bg": "#333", "fg": "white", "activebackground": "#555", "activeforeground": "white"}

frame = tk.Frame(root, bg="#1e1e1e")
frame.pack(padx=10, pady=10, fill='x')

entry = tk.Entry(frame, width=60, font=font_style, bg="#2a2a2a", fg="white", insertbackground="white")
entry.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

tk.Button(frame, text="📂 Durchsuchen", command=browse_file, **btn_style).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
tk.Button(frame, text="📋 Aus Zwischenablage", command=paste_clipboard, **btn_style).grid(row=1, column=1, padx=5, pady=5, sticky="ew")

drop_label = tk.Label(root, text="🎞️ Datei hierher ziehen", font=font_style,
                      relief="groove", width=60, height=7, bg="#2a2a2a", fg="#cccccc")
drop_label.pack(padx=10, pady=5, fill='x')
drop_label.drop_target_register(tkdnd.DND_FILES)
drop_label.dnd_bind('<<Drop>>', on_drop)

big_font_style = ("Segoe UI", 14, "bold")
codec_display = tk.Text(root, height=1, width=60, font=big_font_style, state='disabled',
                        bg="#1e1e1e", fg="white", relief="flat", wrap="none")
codec_display.tag_configure("center", justify='center')
codec_display.tag_config('green', foreground='lime')
codec_display.tag_config('red', foreground='tomato')
codec_display.tag_config('orange', foreground='orange')
codec_display.pack(padx=10, pady=10, fill='both')

if filepath and os.path.isfile(filepath):
    handle_file(filepath)
    
root.mainloop()

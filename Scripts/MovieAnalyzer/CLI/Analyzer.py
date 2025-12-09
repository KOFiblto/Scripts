import json
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from typing import Any, Dict, List, Optional

DEFAULT_VIDEO = "h264"
DEFAULT_AUDIO = "truehd"
DEFAULT_SUBTITLE = "hdmv_pgs_subtitle"

VIDEO_WHITELIST = {"hevc", "h264"}
VIDEO_BLACKLIST = {"mpeg4"}
AUDIO_WHITELIST = {"truehd", "dts", "aac"}
AUDIO_BLACKLIST = {"mp3", "vorbis"}
SUBTITLE_WHITELIST = {"hdmv_pgs_subtitle", "subrip"}
SUBTITLE_BLACKLIST = {"dvd_subtitle"}

COLOR_MAP = {
    'whitelist': 'green',
    'blacklist': 'red',
    'none': 'orange'
}

def has_ffprobe() -> bool:
    return shutil.which("ffprobe") is not None

def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None

def run_ffprobe(path: str) -> Dict[str, Any]:
    cmd = ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", path]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip())
    return json.loads(proc.stdout)

def extract_from_ffprobe(ffjson: Dict[str, Any]) -> Dict[str, List[Dict[str, Optional[str]]]]:
    streams = ffjson.get("streams", [])
    videos, audios, subs = [], [], []
    for s in streams:
        stype = s.get("codec_type")
        tags = s.get("tags") or {}
        language = tags.get("language") or tags.get("LANGUAGE") or "und"
        common = {"index": str(s.get("index")), "codec": s.get("codec_name"), "language": language}
        if stype == "video":
            videos.append(common)
        elif stype == "audio":
            audios.append(common)
        elif stype == "subtitle":
            subs.append(common)
    return {"video": videos, "audio": audios, "subtitle": subs}

def classify_codec(codec: str, whitelist: set, blacklist: set) -> str:
    if codec in whitelist:
        return 'whitelist'
    elif codec in blacklist:
        return 'blacklist'
    else:
        return 'none'

def select_file(entry: tk.Entry):
    filepath = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.mkv *.mov *.avi *.flv *.wmv"), ("All files", "*.*")])
    if filepath:
        entry.delete(0, tk.END)
        entry.insert(0, filepath)

def convert_stream(file_path: str, stream_index: str, stream_type: str):
    if not has_ffmpeg():
        messagebox.showerror("Error", "ffmpeg is not installed or not in PATH.")
        return

    output_file = filedialog.asksaveasfilename(defaultextension=".mkv", filetypes=[("Matroska Video", "*.mkv"), ("All Files", "*.*")])
    if not output_file:
        return

    if stream_type.lower() == "video":
        codec = DEFAULT_VIDEO
    elif stream_type.lower() == "audio":
        codec = DEFAULT_AUDIO
    elif stream_type.lower() == "subtitle":
        codec = DEFAULT_SUBTITLE
    else:
        messagebox.showerror("Error", f"Unknown stream type: {stream_type}")
        return

    stream_letter = {'Video': 'v', 'Audio': 'a', 'Subtitle': 's'}[stream_type]
    cmd = [
        'ffmpeg', '-i', file_path,
        '-map', '0',
        '-c', 'copy',
        f'-c:{stream_letter}:{stream_index}', codec, '-strict', '-2'
        '-map_metadata', '0',
        output_file
    ]

    proc = subprocess.run(cmd, text=True)
    if proc.returncode == 0:
        messagebox.showinfo("Success", f"Stream converted to {codec} and saved to {output_file}")
    else:
        messagebox.showerror("Error", "Conversion failed.")

def analyze_file(path: str, tree: ttk.Treeview):
    for row in tree.get_children():
        tree.delete(row)
    if not has_ffprobe():
        messagebox.showerror("Error", "ffprobe is not installed or not in PATH.")
        return
    try:
        ffjson = run_ffprobe(path)
        info = extract_from_ffprobe(ffjson)
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return

    for v in info["video"]:
        category = classify_codec(v['codec'], VIDEO_WHITELIST, VIDEO_BLACKLIST)
        tree.insert("", "end", values=(f"#{v['index']}", v['codec'], v['language'], "Video", "Convert"), tags=(category,))
    for a in info["audio"]:
        category = classify_codec(a['codec'], AUDIO_WHITELIST, AUDIO_BLACKLIST)
        tree.insert("", "end", values=(f"#{a['index']}", a['codec'], a['language'], "Audio", "Convert"), tags=(category,))
    for s in info["subtitle"]:
        category = classify_codec(s['codec'], SUBTITLE_WHITELIST, SUBTITLE_BLACKLIST)
        tree.insert("", "end", values=(f"#{s['index']}", s['codec'], s['language'], "Subtitle", "Convert"), tags=(category,))

def on_tree_click(event, tree: ttk.Treeview, entry: tk.Entry):
    item = tree.identify_row(event.y)
    column = tree.identify_column(event.x)
    if not item:
        return
    if column == "#5":
        values = tree.item(item, "values")
        index = values[0].lstrip('#')
        stream_type = values[3]
        convert_stream(entry.get(), index, stream_type)

def main():
    root = tk.Tk()
    root.title("Media Stream Inspector")
    root.geometry("800x400")

    frame = tk.Frame(root)
    frame.pack(fill="x", padx=10, pady=5)

    entry = tk.Entry(frame)
    entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
    browse_btn = tk.Button(frame, text="Browse", command=lambda: select_file(entry))
    browse_btn.pack(side="left")

    columns = ("Index", "Codec", "Language", "Type", "Action")
    tree = ttk.Treeview(root, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    tree.tag_configure('whitelist', foreground=COLOR_MAP['whitelist'])
    tree.tag_configure('blacklist', foreground=COLOR_MAP['blacklist'])
    tree.tag_configure('none', foreground=COLOR_MAP['none'])

    tree.bind("<Button-1>", lambda e: on_tree_click(e, tree, entry))

    analyze_btn = tk.Button(frame, text="Analyze", command=lambda: analyze_file(entry.get(), tree))
    analyze_btn.pack(side="left", padx=(5, 0))

    root.mainloop()

if __name__ == "__main__":
    main()
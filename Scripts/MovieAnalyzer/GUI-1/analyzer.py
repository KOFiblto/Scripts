import os
import json
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from fractions import Fraction
import platform

try:
    import ctypes
except ImportError:
    ctypes = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(SCRIPT_DIR, "db")
os.makedirs(DB_DIR, exist_ok=True)

# Colors (Windows 11-inspired style)
BG_DARK = "#1e1e1e"
BG_CARD = "#252526"
COLOR_ACCENT = "#0078d7"  # Windows 11 blue
COLOR_TEXT = "#f3f3f3"
COLOR_TEXT_SECONDARY = "#cccccc"
COLOR_SUPPORTED = "#107c10"  # Green for supported
COLOR_BLACKLIST = "#d13438"  # Red for blacklist
COLOR_UNKNOWN = "#ffc40c"    # Yellow for unknown
COLOR_HIGHLIGHT = "#3a3d41"

FONT_TITLE = ("Segoe UI Semibold", 14)
FONT_NORMAL = ("Segoe UI", 11)
FONT_BUTTON = ("Segoe UI", 10, "bold")

DB_FILES = {
    "video_whitelist": os.path.join(DB_DIR, "video_whitelist.json"),
    "video_blacklist": os.path.join(DB_DIR, "video_blacklist.json"),
    "audio_whitelist": os.path.join(DB_DIR, "audio_whitelist.json"),
    "audio_blacklist": os.path.join(DB_DIR, "audio_blacklist.json"),
    "lang_audio_whitelist": os.path.join(DB_DIR, "lang_audio_whitelist.json"),
    "lang_sub_whitelist": os.path.join(DB_DIR, "lang_sub_whitelist.json"),
}

def load_list(name):
    path = DB_FILES[name]
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_list(name, data):
    with open(DB_FILES[name], "w", encoding="utf-8") as f:
        json.dump(sorted(set(data)), f, indent=2)

def check_ffprobe():
    try:
        subprocess.run(["ffprobe", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

def run_ffprobe(path):
    cmd = ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip() or "ffprobe returned non-zero exit code")
    return json.loads(res.stdout)

def fps_to_float(r_frame_rate):
    try:
        return float(Fraction(r_frame_rate)) if r_frame_rate else None
    except Exception:
        return None

def enable_windows_rounded_corners(root):
    # Windows 11 rounded corners via DWM API
    if platform.system() != "Windows" or not ctypes:
        return
    try:
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWCP_ROUND = 2
        dwmapi = ctypes.windll.dwmapi
        res = dwmapi.DwmSetWindowAttribute(hwnd,
                                          DWMWA_WINDOW_CORNER_PREFERENCE,
                                          ctypes.byref(ctypes.c_int(DWMWCP_ROUND)),
                                          ctypes.sizeof(ctypes.c_int))
        # If needed, you can check res == 0 for success
    except Exception:
        pass  # silently fail if anything goes wrong

class RoundedButton(ttk.Button):
    # Use ttk styles to simulate rounded buttons by padding + background colors
    def __init__(self, master=None, **kw):
        super().__init__(master, style="Rounded.TButton", **kw)

class MovieInfoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Movie Info Inspector")
        self.geometry("1000x720")
        self.configure(bg=BG_DARK)

        self.style = ttk.Style(self)
        self.style.theme_use('clam')

        self._setup_styles()
        enable_windows_rounded_corners(self)

        if not check_ffprobe():
            messagebox.showerror("FFprobe missing", "ffprobe not found in PATH")
            self.destroy()
            sys.exit(1)
        self._build()

    def _setup_styles(self):
        s = self.style
        # Rounded button style simulation
        s.configure("Rounded.TButton",
                    foreground=COLOR_TEXT,
                    background=COLOR_ACCENT,
                    font=FONT_BUTTON,
                    padding=8,
                    relief="flat")
        s.map("Rounded.TButton",
              foreground=[("active", COLOR_TEXT), ("disabled", COLOR_TEXT_SECONDARY)],
              background=[("active", "#005a9e"), ("disabled", "#3a3d41")])

        # Frame style
        s.configure("Card.TFrame", background=BG_CARD, relief="flat")
        s.configure("Main.TFrame", background=BG_DARK)
        # Label styles
        s.configure("Title.TLabel", background=BG_DARK, foreground=COLOR_TEXT, font=FONT_TITLE)
        s.configure("CardTitle.TLabel", background=BG_CARD, foreground=COLOR_ACCENT, font=FONT_TITLE)
        s.configure("CardInfo.TLabel", background=BG_CARD, foreground=COLOR_TEXT_SECONDARY, font=FONT_NORMAL)
        s.configure("StatusSupported.TLabel", background=COLOR_SUPPORTED, foreground="white", font=FONT_NORMAL)
        s.configure("StatusBlacklist.TLabel", background=COLOR_BLACKLIST, foreground="white", font=FONT_NORMAL)
        s.configure("StatusUnknown.TLabel", background=COLOR_UNKNOWN, foreground="black", font=FONT_NORMAL)
        s.configure("LangSupported.TLabel", background=COLOR_SUPPORTED, foreground="white", font=FONT_NORMAL)
        s.configure("LangUnknown.TLabel", background=COLOR_UNKNOWN, foreground="black", font=FONT_NORMAL)
        s.configure("Listbox.TListbox", background=BG_CARD, foreground=COLOR_TEXT)

    def _build(self):
        top_frame = ttk.Frame(self, style="Main.TFrame")
        top_frame.pack(fill=tk.X, pady=10, padx=10)
        RoundedButton(top_frame, text="Choose Media File", command=self.open_file).pack(side=tk.LEFT)
        self.file_label = ttk.Label(top_frame, text="No file loaded", style="Title.TLabel", anchor='w')
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(15,0))

        self.card_frame = ttk.Frame(self, style="Main.TFrame")
        self.card_frame.pack(fill=tk.X, pady=10, padx=10)

        self.subtitle_frame = ttk.Frame(self, style="Main.TFrame")
        self.subtitle_frame.pack(fill=tk.X, pady=10, padx=10)

        bottom_frame = ttk.Frame(self, style="Main.TFrame")
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)

        # Use grid for better horizontal stretching
        bottom_frame.columnconfigure(0, weight=3)  # video frame wide
        bottom_frame.columnconfigure(1, weight=3)  # audio frame wide
        bottom_frame.columnconfigure(2, weight=2)  # language frame smaller

        self.video_list_frame = self._create_list_frame(bottom_frame, "Video Codecs", "video")
        self.video_list_frame.grid(row=0, column=0, sticky="nsew", padx=5)

        self.audio_list_frame = self._create_list_frame(bottom_frame, "Audio Codecs", "audio")
        self.audio_list_frame.grid(row=0, column=1, sticky="nsew", padx=5)

        lang_frame = ttk.Frame(bottom_frame, style="Main.TFrame")
        lang_frame.grid(row=0, column=2, sticky="nsew", padx=5)
        lang_frame.columnconfigure(0, weight=1)
        lang_frame.rowconfigure(0, weight=1)
        lang_frame.rowconfigure(1, weight=1)
        self.lang_audio_frame = self._create_list_frame(lang_frame, "Audio Languages", "lang_audio")
        self.lang_audio_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.lang_sub_frame = self._create_list_frame(lang_frame, "Subtitle Languages", "lang_sub")
        self.lang_sub_frame.pack(fill=tk.BOTH, expand=True, pady=5)

    def _create_list_frame(self, parent, title, category):
        frame = ttk.Frame(parent, style="Card.TFrame", padding=8)
        # Don't pack here if using grid; caller handles it
        ttk.Label(frame, text=title, style="CardTitle.TLabel").pack(fill=tk.X, pady=(0,8))

        listbox = tk.Listbox(frame, bg=BG_CARD, fg=COLOR_TEXT, selectbackground=COLOR_ACCENT,
                             activestyle='none', highlightthickness=0, relief=tk.FLAT, font=FONT_NORMAL)
        listbox.pack(fill=tk.BOTH, expand=True, pady=(0,8))

        btn_frame = ttk.Frame(frame, style="Card.TFrame")
        btn_frame.pack(fill=tk.X)

        RoundedButton(btn_frame, text="+WL",
                      command=lambda: self._add_item(category, "whitelist", listbox)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,4))

        if "lang" not in category:
            RoundedButton(btn_frame, text="+BL",
                          command=lambda: self._add_item(category, "blacklist", listbox)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)

        RoundedButton(btn_frame, text="Del",
                      command=lambda: self._delete_item(category, listbox)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(4,0))

        self._refresh_list(category, listbox)
        return frame

    def _refresh_list(self, category, listbox_frame):
        # listbox_frame is the Frame, find the Listbox inside
        listbox = None
        for child in listbox_frame.winfo_children():
            if isinstance(child, tk.Listbox):
                listbox = child
                break
        if listbox is None:
            return
        listbox.delete(0, tk.END)
        if "lang" in category:
            data = load_list(f"{category}_whitelist")
            for item in data:
                listbox.insert(tk.END, item)
                listbox.itemconfig(tk.END, bg=COLOR_SUPPORTED, fg="white")
        else:
            wl = load_list(f"{category}_whitelist")
            bl = load_list(f"{category}_blacklist")
            for item in wl:
                listbox.insert(tk.END, item)
                listbox.itemconfig(tk.END, bg=COLOR_SUPPORTED, fg="white")
            for item in bl:
                listbox.insert(tk.END, item)
                listbox.itemconfig(tk.END, bg=COLOR_BLACKLIST, fg="white")

    def _add_item(self, category, list_type, listbox_frame):
        val = simpledialog.askstring("Add", f"Enter {category} to add to {list_type}:")
        if not val:
            return
        data = load_list(f"{category}_{list_type}")
        data.append(val.lower())
        save_list(f"{category}_{list_type}", data)
        self._refresh_list(category, listbox_frame)

    def _delete_item(self, category, listbox_frame):
        listbox = None
        for child in listbox_frame.winfo_children():
            if isinstance(child, tk.Listbox):
                listbox = child
                break
        if not listbox:
            return
        sel = listbox.curselection()
        if not sel:
            return
        val = listbox.get(sel[0]).lower()
        if "lang" in category:
            data = load_list(f"{category}_whitelist")
            if val in data:
                data.remove(val)
                save_list(f"{category}_whitelist", data)
        else:
            for lt in ["whitelist", "blacklist"]:
                data = load_list(f"{category}_{lt}")
                if val in data:
                    data.remove(val)
                    save_list(f"{category}_{lt}", data)
        self._refresh_list(category, listbox_frame)

    def _codec_status(self, codec):
        codec_l = codec.lower()
        if codec_l in load_list('video_whitelist') or codec_l in load_list('audio_whitelist'):
            return ("Supported", COLOR_SUPPORTED)
        if codec_l in load_list('video_blacklist') or codec_l in load_list('audio_blacklist'):
            return ("Blacklisted", COLOR_BLACKLIST)
        return ("Unknown", COLOR_UNKNOWN)

    def _lang_status(self, lang, category):
        whitelist = load_list(f"{category}_whitelist")
        if lang.lower() in whitelist:
            return ("Supported", COLOR_SUPPORTED)
        return ("Unknown", COLOR_UNKNOWN)

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Media files", "*.mp4 *.mkv *.avi *.mov *.flv *.webm"), ("All files", "*.*")])
        if not path: return
        self.file_label.config(text=path)
        self._load_info(path)

    def _clear_cards(self):
        for w in self.card_frame.winfo_children(): w.destroy()
        for w in self.subtitle_frame.winfo_children(): w.destroy()

    def _create_card(self, title, codec, lang, extra_info=None):
        status_text, color = self._codec_status(codec)
        card = ttk.Frame(self.card_frame, style="Card.TFrame", padding=10)
        card.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.Y)

        ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor='w', pady=(0,4))
        lbl_codec = ttk.Label(card, text=f"Codec: {codec}", background=color, foreground="white", font=FONT_NORMAL)
        lbl_codec.pack(anchor='w', fill=tk.X, pady=2, ipady=3, padx=4)
        ttk.Label(card, text=f"Status: {status_text}", style="CardInfo.TLabel").pack(anchor='w')

        if lang:
            if title == "Audio":
                _, lang_color = self._lang_status(lang, 'lang_audio')
            elif title == "Subtitle":
                _, lang_color = self._lang_status(lang, 'lang_sub')
            else:
                lang_color = COLOR_UNKNOWN
            lbl_lang = ttk.Label(card, text=f"Language: {lang.upper()}", background=lang_color,
                                foreground="white" if lang_color != COLOR_UNKNOWN else "black", font=FONT_NORMAL)
            lbl_lang.pack(anchor='w', fill=tk.X, pady=2, ipady=3, padx=4)

        if extra_info:
            ttk.Label(card, text=extra_info, style="CardInfo.TLabel").pack(anchor='w', pady=(4,0))

    def _load_info(self, path):
        self._clear_cards()
        try:
            info = run_ffprobe(path)
        except Exception as e:
            messagebox.showerror('Error', f'ffprobe failed: {e}')
            return

        video_streams = [s for s in info.get('streams', []) if s.get('codec_type') == 'video']
        audio_streams = [s for s in info.get('streams', []) if s.get('codec_type') == 'audio']
        subtitle_streams = [s for s in info.get('streams', []) if s.get('codec_type') == 'subtitle']

        # Video cards
        for v in video_streams:
            codec = v.get('codec_name', 'unknown')
            width = v.get('width', 0)
            height = v.get('height', 0)
            fps = fps_to_float(v.get('r_frame_rate'))
            extra = f"{width}x{height}"
            if fps:
                extra += f" @ {fps:.2f} fps"
            self._create_card("Video", codec, None, extra)

        # Audio cards
        for a in audio_streams:
            codec = a.get('codec_name', 'unknown')
            lang = a.get('tags', {}).get('language') if a.get('tags') else None
            channels = a.get('channels', '?')
            sr = a.get('sample_rate', '?')
            extra = f"Channels: {channels}, Sample Rate: {sr}"
            self._create_card("Audio", codec, lang, extra)

        # Subtitle cards
        for s in subtitle_streams:
            codec = s.get('codec_name', 'unknown')
            lang = s.get('tags', {}).get('language') if s.get('tags') else None
            self._create_card("Subtitle", codec, lang)

app = MovieInfoApp()
app.mainloop()

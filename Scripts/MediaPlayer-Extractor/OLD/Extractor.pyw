import tkinter as tk
from tkinter import filedialog, ttk
import subprocess
import os
from datetime import timedelta

# -------- CONFIG --------
ROOT_OUTPUT_FOLDER = r"C:\_other\Celebs\Extractor"
FFMPEG_PATH = "ffmpeg"  # Ensure ffmpeg is in PATH or provide full path
# ------------------------

# --- Functions ---
def browse_file():
    file_path = filedialog.askopenfilename(
        title="Select a movie file",
        filetypes=[("Video files", "*.mp4 *.mkv *.avi *.mov *.flv *.wmv"), ("All files", "*.*")]
    )
    if file_path:
        entry_file_var.set(file_path)
        reset_status()

def get_movie_folder(file_path):
    movie_name = os.path.splitext(os.path.basename(file_path))[0]
    folder = os.path.join(ROOT_OUTPUT_FOLDER, movie_name)
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder

def reset_status(*args):
    status_label.config(text="", bg=root.cget("bg"))

def update_status(message, success=True):
    status_label.config(text=message, bg="green" if success else "red", fg="white")

def str_to_timedelta(time_str):
    """Convert time string to timedelta. Supports HH:MM:SS, MM:SS, or with milliseconds."""
    parts = time_str.split(":")
    try:
        if len(parts) == 3:
            h, m, s = parts
        elif len(parts) == 2:
            h = 0
            m, s = parts
        elif len(parts) == 1:
            h = 0
            m = 0
            s = parts[0]
        else:
            raise ValueError("Invalid time format")
        
        if "." in s:
            sec, ms = s.split(".")
            return timedelta(hours=int(h), minutes=int(m), seconds=int(sec), milliseconds=int(ms))
        return timedelta(hours=int(h), minutes=int(m), seconds=int(s))
    except Exception as e:
        raise ValueError(f"Cannot parse time '{time_str}': {e}")


def extract_segment():
    file_path = entry_file_var.get().strip()
    start_time = entry_start_var.get().strip()
    end_time = entry_end_var.get().strip()
    scene_name = entry_scene_var.get().strip()

    reset_status()

    if not file_path or not os.path.isfile(file_path):
        update_status("Invalid movie file.", success=False)
        return
    if not start_time or not end_time:
        update_status("Please enter both start and end timestamps.", success=False)
        return
    if not scene_name:
        update_status("Please enter a scene name.", success=False)
        return

    # Calculate duration
    try:
        start_td = str_to_timedelta(start_time)
        end_td = str_to_timedelta(end_time)
    except Exception as e:
        update_status(f"Time parsing error: {e}", success=False)
        return

    duration_td = end_td - start_td
    if duration_td.total_seconds() <= 0:
        update_status("End time must be after start time.", success=False)
        return
    duration_str = str(duration_td)

    output_folder = get_movie_folder(file_path)
    _, ext = os.path.splitext(file_path)
    safe_scene_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in scene_name).strip()
    safe_start = start_time.replace(":", "-").replace(".", "_")
    safe_end = end_time.replace(":", "-").replace(".", "_")
    output_file = os.path.join(output_folder, f"{safe_scene_name}_{safe_start}_{safe_end}{ext}")

    # Option 1: -ss before -i, use -t for duration
    command = [
        FFMPEG_PATH, "-y",
        "-ss", start_time,
        "-i", file_path,
        "-t", str(duration_td.total_seconds()),
        "-c:v", "libx264",  # re-encode video
        "-c:a", "aac",      # re-encode audio
        output_file
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        update_status(f"Segment saved to {output_file}", success=True)
    except subprocess.CalledProcessError as e:
    	update_status(f"Failed: {e.stderr}", success=False)

def extract_image():
    file_path = entry_file_var.get().strip()
    timestamp = entry_start_var.get().strip()
    image_name = entry_scene_var.get().strip()

    reset_status()

    if not file_path or not os.path.isfile(file_path):
        update_status("Invalid movie file.", success=False)
        return
    if not timestamp:
        update_status("Please enter a timestamp.", success=False)
        return
    if not image_name:
        update_status("Please enter an image name.", success=False)
        return

    output_folder = get_movie_folder(file_path)
    
    # Safe naming
    safe_image_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in image_name).strip()
    safe_timestamp = timestamp.replace(":", "-").replace(".", "_")
    
    output_file = os.path.join(output_folder, f"{safe_image_name}_{safe_timestamp}.png")
    
    command = [FFMPEG_PATH, "-y", "-ss", timestamp, "-i", file_path, "-vframes", "1", output_file]
    
    try:
        subprocess.run(command, check=True)
        update_status(f"Image saved to {output_file}", success=True)
    except subprocess.CalledProcessError:
        update_status("Failed to extract image.", success=False)


# --- GUI Setup ---
root = tk.Tk()
root.title("Media Extractor (Video Segments & Images)")
root.geometry("700x400")
root.configure(bg="#1e1e1e")  # Dark background

# --- Fonts & Styles ---
default_font = ("Segoe UI", 10)
heading_font = ("Segoe UI Semibold", 11)

style = ttk.Style(root)
style.theme_use('clam')
style.configure("TNotebook", background="#1e1e1e", borderwidth=0)
style.configure("TNotebook.Tab", background="#2a2a2a", foreground="white", padding=[12, 8])
style.map("TNotebook.Tab", background=[("selected", "#0078d7")], foreground=[("selected", "white")])
style.configure("TButton", font=default_font, padding=5)
style.configure("TLabel", background="#1e1e1e", foreground="white")
style.configure("TEntry", fieldbackground="#2a2a2a", foreground="white")

# --- Variables ---
entry_file_var = tk.StringVar()
entry_start_var = tk.StringVar()
entry_end_var = tk.StringVar()
entry_scene_var = tk.StringVar()

def bind_reset(widget, var=None):
    widget.bind("<Key>", reset_status)
    widget.bind("<Button-1>", reset_status)
    if var:
        var.trace_add("write", reset_status)

# --- Notebook ---
notebook = ttk.Notebook(root)
notebook.pack(padx=15, pady=15, fill="both", expand=True)

# --- Segment Tab ---
tab_segment = ttk.Frame(notebook)
notebook.add(tab_segment, text="Video Segment")

tk.Label(tab_segment, text="Movie file:", font=heading_font).grid(row=0, column=0, sticky="w", pady=5)
entry_segment_file = tk.Entry(tab_segment, width=50, textvariable=entry_file_var)
entry_segment_file.grid(row=0, column=1, padx=5, pady=5)
tk.Button(tab_segment, text="Browse", command=browse_file).grid(row=0, column=2)
bind_reset(entry_segment_file, entry_file_var)

tk.Label(tab_segment, text="Start time (HH:MM:SS.mmm):", font=heading_font).grid(row=1, column=0, sticky="w", pady=5)
entry_start = tk.Entry(tab_segment, width=20, textvariable=entry_start_var)
entry_start.grid(row=1, column=1, sticky="w", pady=5)
bind_reset(entry_start, entry_start_var)

tk.Label(tab_segment, text="End time (HH:MM:SS.mmm):", font=heading_font).grid(row=2, column=0, sticky="w", pady=5)
entry_end = tk.Entry(tab_segment, width=20, textvariable=entry_end_var)
entry_end.grid(row=2, column=1, sticky="w", pady=5)
bind_reset(entry_end, entry_end_var)

tk.Label(tab_segment, text="Scene name:", font=heading_font).grid(row=3, column=0, sticky="w", pady=5)
entry_scene_name = tk.Entry(tab_segment, width=30, textvariable=entry_scene_var)
entry_scene_name.grid(row=3, column=1, sticky="w", pady=5)
bind_reset(entry_scene_name, entry_scene_var)

tk.Button(tab_segment, text="Extract Segment", command=extract_segment, bg="#0078d7", fg="white").grid(row=4, column=0, columnspan=3, pady=15, ipadx=10)

# --- Image Tab ---
tab_image = ttk.Frame(notebook)
notebook.add(tab_image, text="Image Extractor")

tk.Label(tab_image, text="Movie file:", font=heading_font).grid(row=0, column=0, sticky="w", pady=5)
entry_image_file = tk.Entry(tab_image, width=50, textvariable=entry_file_var)
entry_image_file.grid(row=0, column=1, padx=5, pady=5)
tk.Button(tab_image, text="Browse", command=browse_file).grid(row=0, column=2)
bind_reset(entry_image_file, entry_file_var)

tk.Label(tab_image, text="Timestamp (HH:MM:SS.mmm):", font=heading_font).grid(row=1, column=0, sticky="w", pady=5)
entry_timestamp = tk.Entry(tab_image, width=20, textvariable=entry_start_var)
entry_timestamp.grid(row=1, column=1, sticky="w", pady=5)
bind_reset(entry_timestamp, entry_start_var)

tk.Label(tab_image, text="Image name:", font=heading_font).grid(row=2, column=0, sticky="w", pady=5)
entry_image_name = tk.Entry(tab_image, width=30, textvariable=entry_scene_var)
entry_image_name.grid(row=2, column=1, sticky="w", pady=5)
bind_reset(entry_image_name, entry_scene_var)

tk.Button(tab_image, text="Extract Image", command=extract_image, bg="#0078d7", fg="white").grid(row=3, column=0, columnspan=3, pady=15, ipadx=10)

# --- Status Bar ---
status_label = tk.Label(root, text="", anchor="w", bg="#1e1e1e", fg="white")
status_label.pack(fill="x", side="bottom")

root.mainloop()

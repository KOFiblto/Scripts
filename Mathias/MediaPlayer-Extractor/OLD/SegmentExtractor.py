import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os

# -------- CONFIG --------
OUTPUT_FOLDER = r"C:\_other\Celebs\SegmentExtractor"  # Change to your desired folder
FFMPEG_PATH = "ffmpeg"  # Ensure ffmpeg is in PATH or provide full path
# ------------------------

def browse_file():
    file_path = filedialog.askopenfilename(
        title="Select a movie file",
        filetypes=[("Video files", "*.mp4 *.mkv *.avi *.mov *.flv *.wmv"), ("All files", "*.*")]
    )
    if file_path:
        entry_file.delete(0, tk.END)
        entry_file.insert(0, file_path)

def extract_segment():
    file_path = entry_file.get().strip()
    start_time = entry_start.get().strip()
    end_time = entry_end.get().strip()
    scene_name = entry_name.get().strip()

    if not file_path or not os.path.isfile(file_path):
        messagebox.showerror("Error", "Please select a valid movie file.")
        return

    if not start_time or not end_time:
        messagebox.showerror("Error", "Please enter both start and end timestamps.")
        return

    if not scene_name:
        messagebox.showerror("Error", "Please enter a scene name.")
        return

    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    # Keep original file extension
    _, ext = os.path.splitext(file_path)

    # Allow spaces in scene name, but make filename safe for filesystem
    safe_scene_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in scene_name)
    safe_scene_name = safe_scene_name.strip().replace("  ", " ")

    # Replace invalid filename characters, keeping milliseconds safe
    safe_start = start_time.replace(":", "-").replace(".", "_")
    safe_end = end_time.replace(":", "-").replace(".", "_")

    # Use only scene name + times for output file
    output_file = os.path.join(OUTPUT_FOLDER, f"{safe_scene_name}_{safe_start}_{safe_end}{ext}")

    command = [
        FFMPEG_PATH, "-y",
        "-ss", start_time,
        "-to", end_time,
        "-i", file_path,
        "-c", "copy",
        output_file
    ]

    try:
        subprocess.run(command, check=True)
        messagebox.showinfo("Success", f"Segment saved to:\n{output_file}")
    except subprocess.CalledProcessError:
        messagebox.showerror("Error", "Failed to extract video segment. Check ffmpeg installation.")

# --- GUI Setup ---
root = tk.Tk()
root.title("Video Segment Extractor (Milliseconds)")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack()

# Movie file selection
tk.Label(frame, text="Movie file:").grid(row=0, column=0, sticky="w")
entry_file = tk.Entry(frame, width=50)
entry_file.grid(row=0, column=1, padx=5)
tk.Button(frame, text="Browse", command=browse_file).grid(row=0, column=2)

# Start timestamp
tk.Label(frame, text="Start time (HH:MM:SS.mmm):").grid(row=1, column=0, sticky="w")
entry_start = tk.Entry(frame, width=15)
entry_start.grid(row=1, column=1, sticky="w")

# End timestamp
tk.Label(frame, text="End time (HH:MM:SS.mmm):").grid(row=2, column=0, sticky="w")
entry_end = tk.Entry(frame, width=15)
entry_end.grid(row=2, column=1, sticky="w")

# Scene name
tk.Label(frame, text="Scene name:").grid(row=3, column=0, sticky="w")
entry_name = tk.Entry(frame, width=30)
entry_name.grid(row=3, column=1, sticky="w")

# Extract button
tk.Button(frame, text="Extract Segment", command=extract_segment, bg="lightgreen").grid(row=4, column=0, columnspan=3, pady=10)

root.mainloop()

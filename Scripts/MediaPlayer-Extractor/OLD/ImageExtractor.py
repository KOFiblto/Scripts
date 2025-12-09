import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os

# -------- CONFIG --------
OUTPUT_FOLDER = r"C:\_other\Celebs\ImageExtractor"  # Change to your desired folder
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

def extract_image():
    file_path = entry_file.get().strip()
    timestamp = entry_time.get().strip()
    image_name = entry_name.get().strip()

    if not file_path or not os.path.isfile(file_path):
        messagebox.showerror("Error", "Please select a valid movie file.")
        return

    if not timestamp:
        messagebox.showerror("Error", "Please enter a timestamp (HH:MM:SS.mmm).")
        return

    if not image_name:
        messagebox.showerror("Error", "Please enter an image name.")
        return

    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    # Make a safe filename
    safe_image_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in image_name)
    safe_image_name = safe_image_name.strip().replace("  ", " ")

    # Replace ':' with '-' in the timestamp, but keep milliseconds safe for filename
    safe_time = timestamp.replace(":", "-").replace(".", "_")

    output_file = os.path.join(OUTPUT_FOLDER, f"{safe_image_name}_{safe_time}.jpg")

    command = [
        FFMPEG_PATH, "-y",
        "-ss", timestamp,
        "-i", file_path,
        "-vframes", "1",  # Only one frame
        "-q:v", "2",      # Quality: lower = better
        output_file
    ]

    try:
        subprocess.run(command, check=True)
        messagebox.showinfo("Success", f"Image saved to:\n{output_file}")
    except subprocess.CalledProcessError:
        messagebox.showerror("Error", "Failed to extract image. Check ffmpeg installation.")

# --- GUI Setup ---
root = tk.Tk()
root.title("Image Extractor")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack()

# Movie file selection
tk.Label(frame, text="Movie file:").grid(row=0, column=0, sticky="w")
entry_file = tk.Entry(frame, width=50)
entry_file.grid(row=0, column=1, padx=5)
tk.Button(frame, text="Browse", command=browse_file).grid(row=0, column=2)

# Timestamp (HH:MM:SS.mmm)
tk.Label(frame, text="Timestamp (HH:MM:SS.mmm):").grid(row=1, column=0, sticky="w")
entry_time = tk.Entry(frame, width=20)
entry_time.grid(row=1, column=1, sticky="w")

# Image name
tk.Label(frame, text="Image name:").grid(row=2, column=0, sticky="w")
entry_name = tk.Entry(frame, width=30)
entry_name.grid(row=2, column=1, sticky="w")

# Extract button
tk.Button(frame, text="Extract Image", command=extract_image, bg="lightblue").grid(row=3, column=0, columnspan=3, pady=10)

root.mainloop()

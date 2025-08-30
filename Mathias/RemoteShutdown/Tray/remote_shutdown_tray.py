import threading
import webbrowser
from flask import Flask, render_template_string, redirect, url_for
import pystray
from PIL import Image, ImageDraw

app = Flask(__name__)

PRINT = 0
def customprint(text):
    if PRINT:
        print(text)

# ===== Flask Routes =====
@app.route("/sonarr")
def sonarr():
    customprint("Opening Sonarr")
    return redirect("http://192.168.178.21:8989")

@app.route("/radarr")
def radarr():
    customprint("Opening Radarr")
    return redirect("http://192.168.178.21:7878")

@app.route("/sabnzbd")
def sabnzbd():
    customprint("Opening SABnzbd")
    return redirect("http://192.168.178.21:6969")

@app.route("/jellyfin")
def jellyfin():
    customprint("Opening Jellyfin")
    return redirect("http://192.168.178.21:8096")

@app.route("/shutdown")
def shutdown():
    os.system("shutdown /s /t 0")
    customprint("Shutting down")
    return "Shutting down..."

# ===== Run Flask in a background thread =====
def run_flask():
    app.run(host="0.0.0.0", port=5000)

flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# ===== System Tray Menu =====
def create_image():
    """Simple tray icon: black with white circle"""
    image = Image.new("RGB", (64, 64), color="black")
    dc = ImageDraw.Draw(image)
    dc.ellipse((16, 16, 48, 48), fill="white")
    return image

def open_sonarr(icon, item):
    webbrowser.open("http://192.168.178.21:8989")

def open_radarr(icon, item):
    webbrowser.open("http://192.168.178.21:7878")

def open_sabnzbd(icon, item):
    webbrowser.open("http://192.168.178.21:6969")

def open_jellyfin(icon, item):
    webbrowser.open("http://192.168.178.21:8096")

def shutdown_pc(icon, item):
    customprint("Shutdown clicked!")
    # os.system("shutdown /s /t 0")

def quit_program(icon, item):
    icon.stop()
    customprint("Tray app exited")

menu = pystray.Menu(
    pystray.MenuItem("Sonarr", open_sonarr),
    pystray.MenuItem("Radarr", open_radarr),
    pystray.MenuItem("SABnzbd", open_sabnzbd),
    pystray.MenuItem("Jellyfin", open_jellyfin),
    pystray.MenuItem("Shutdown PC", shutdown_pc),
    pystray.MenuItem("Quit", quit_program)
)

icon = pystray.Icon("RemoteShutdown", create_image(), "Remote Shutdown", menu)
icon.run()

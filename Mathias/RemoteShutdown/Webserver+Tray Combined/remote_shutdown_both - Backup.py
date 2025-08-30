import threading
import wx
import webbrowser
from flask import Flask, render_template_string, redirect, url_for
import pystray
from PIL import Image, ImageDraw
import os
import logging
import ctypes


# ===== Logging =====
logging.basicConfig(filename="server.log", level=logging.INFO,
                    format="%(asctime)s %(levelname)s: %(message)s")

app = Flask(__name__)
PRINT = 0

def customprint(text):
    if PRINT:
        print(text)
    logging.info(text)

# ===== Flask Routes =====
@app.route("/sonarr")
def sonarr():
    customprint("Opening Sonarr")
    return redirect("http://localhost:8989")

@app.route("/radarr")
def radarr():
    customprint("Opening Radarr")
    return redirect("http://localhost:7878")

@app.route("/sabnzbd")
def sabnzbd():
    customprint("Opening SABnzbd")
    return redirect("http://localhost:6969")

@app.route("/jellyfin")
def jellyfin():
    customprint("Opening Jellyfin")
    return redirect("http://localhost:8096")

@app.route("/jellyseerr")
def jellyseerr():
    customprint("Opening Jellyseerr")
    return redirect("http://localhost:5055")

@app.route("/jellyseerr-start")
def jellyseerr_start():
    customprint("Starting Jellyseerr")
    os.system(r'start "" "D:\\Scripts\\Jellyserr\\start_jellyserr.vbs"')
    return "Starting Jellyseerr..."

@app.route("/jellyseerr-stop")
def jellyseerr_stop():
    customprint("Stopping Jellyseerr")
    os.system(r'start "" "D:\\Scripts\\Jellyserr\\stop_jellyserr.vbs"')
    return "Stopping Jellyseerr..."

@app.route("/shutdown")
def shutdown():
    os.system("shutdown /s /f /t 0")
    customprint("Shutting down...")
    return "Shutting down..."

# ===== Status endpoint =====
@app.route("/status")
def status():
    return "online"

# ===== Homepage UI =====
@app.route("/")
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Server Control</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                background-color: #f4f4f4;
                margin: 0;
                padding: 1rem;
                display: flex;
                flex-direction: column;
                align-items: center;
                min-height: 100vh;
            }
            h1 {
                margin-bottom: 1rem;
                font-size: 2.5rem;
            }
            .btn, .btn-row { box-sizing: border-box; }
            .btn {
                display: flex;
                align-items: center;
                justify-content: center;
                width: min(90%, 600px);
                margin: 0.5rem 0;
                padding: 1rem;
                font-size: 2rem;
                min-height: 5vh;
                max-height: 6vh;
                text-decoration: none;
                color: white;
                background: #007BFF;
                border-radius: 1rem;
                transition: background 0.2s;
                cursor: pointer;
            }
            .btn img {
                max-height: 3rem;
                width: auto;
                margin-right: 1rem;
            }
            .btn:hover { background: #0056b3; }
            .btn-danger { background: #dc3545; }
            .btn-danger:hover { background: #a71d2a; }
            .btn-green { background: #28a745; }
            .btn-green:hover { background: #1e7e34; }
            .btn-red { background: #db4251; }
            .btn-red:hover { background: #a71d2a; }
            .btn-row {
                display: flex;
                justify-content: space-between;
                width: min(90%, 600px);
                margin: 0.5rem 0;
                gap: 50px;
            }
            .btn-half { flex: 1; }
            .btn-half img { max-height: 2.5rem; }
            #status-box {
                margin-top: 1rem;
                padding: 1rem 2rem;
                border-radius: 1rem;
                font-size: 2.5rem;
                font-weight: bold;
                color: white;
                min-width: 250px;
            }
            @media (max-width: 1000px) {
                .btn {
                    font-size: 3rem;
                    min-height: 6vh;
                    max-height: 13vh;
                    padding: 1rem;
                    flex-direction: row;
                    width: calc(100% - 20px);
                    margin: 1rem 10px;
                }
                .btn img {
                    max-height: 4rem;
                    margin-right: 1rem;
                }
                h1 { font-size: 2.5rem; }
                #status-box { font-size: 3rem; }
            }
        </style>
    </head>
    <body>
        <h1>Mathias Laptop</h1>
        <a class="btn" href="/sonarr"><img src="{{ url_for('static', filename='img/sonarr.png') }}" alt="Sonarr"> Sonarr</a>
        <a class="btn" href="/radarr"><img src="{{ url_for('static', filename='img/radarr.png') }}" alt="Radarr"> Radarr</a>
        <a class="btn" href="/sabnzbd"><img src="{{ url_for('static', filename='img/sabnzbd.png') }}" alt="SABnzbd"> SABnzbd</a>
        <a class="btn" href="/jellyfin"><img src="{{ url_for('static', filename='img/jellyfin.png') }}" alt="Jellyfin"> Jellyfin</a>
        <a class="btn" href="/jellyseerr"><img src="{{ url_for('static', filename='img/jellyseerr.png') }}" alt="Jellyseerr"> Jellyseerr</a>
        <div class="btn-row">
            <a class="btn btn-half btn-green" href="/jellyseerr-start"><img src="{{ url_for('static', filename='img/jellyseerr.png') }}" alt="Start Jellyseerr"> Start</a>
            <a class="btn btn-half btn-red" href="/jellyseerr-stop"><img src="{{ url_for('static', filename='img/jellyseerr.png') }}" alt="Stop Jellyseerr"> Stop</a>
        </div>
        <a class="btn btn-danger" href="javascript:void(0);" onclick="shutdown()"><img src="{{ url_for('static', filename='img/shutdown.png') }}" alt="Shutdown"> Shutdown</a>
        <div id="status-box">Loading... <span id="flash-dot">•</span></div>
        <script>
            const statusBox = document.getElementById("status-box");
            const flashDot = document.getElementById("flash-dot");
            let statusInterval = null;
            function flash() {
                flashDot.style.opacity = "1";
                setTimeout(() => { flashDot.style.opacity = "0"; }, 200);
            }
            function checkStatus() {
                fetch('/status', {cache: "no-store"})
                    .then(response => response.text())
                    .then(data => {
                        statusBox.innerText = "Online";
                        statusBox.appendChild(flashDot);
                        statusBox.style.backgroundColor = "green";
                        flash();
                    })
                    .catch(error => {
                        statusBox.innerText = "Not Responding";
                        statusBox.appendChild(flashDot);
                        statusBox.style.backgroundColor = "red";
                        flash();
                    });
            }
            function shutdown() {
            
                if (!confirm("Are you sure you want to shut down this PC?")) {
                    return; // cancel if user clicks "Cancel"
                }
                clearInterval(statusInterval);
                statusBox.innerText = "Shutting down...";
                statusBox.appendChild(flashDot);
                statusBox.style.backgroundColor = "orange";
                setTimeout(() => { statusInterval = setInterval(checkStatus, 1000); }, 3000);
                fetch('/shutdown')
                    .then(response => response.text())
                    .then(data => console.log(data))
                    .catch(error => console.log(error));
            }
            statusInterval = setInterval(checkStatus, 1000);
            flashDot.style.transition = "opacity 0.1s";
            flashDot.style.opacity = "0";
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

# ===== Flask background thread (using Waitress) =====
def run_flask():
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000, threads=2)

flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# ===== System Tray =====
def create_icon_image():
    img = Image.new("RGB", (64,64), "black")
    d = ImageDraw.Draw(img)
    d.ellipse((16,16,48,48), fill="white")
    return img

def open_url(url):
    webbrowser.open(url)

def quit_program(icon, item):
    icon.stop()
    
def confirm_shutdown_threaded():
    def _shutdown():
        result = ctypes.windll.user32.MessageBoxW(
            None,
            "Are you sure you want to shut down this PC?",
            "Confirm Shutdown",
            1
        )
        if result == 1:  # OK pressed
            os.system("shutdown /s /f /t 1")

    threading.Thread(target=_shutdown).start()

def load_icon(path, size=(16, 16)):
    """Load an image from disk and resize for tray menu."""
    img = Image.open(path)
    img = img.resize(size, Image.LANCZOS)
    return img
    
tray_menu = pystray.Menu(
    pystray.MenuItem("⚪ Sonarr", lambda icon, item: open_url("http://localhost:8989")),
    pystray.MenuItem("🟡 Radarr", lambda icon, item: open_url("http://localhost:7878")),
    pystray.MenuItem("🟣 Jellyfin", lambda icon, item: open_url("http://localhost:8096")),
    pystray.MenuItem("🟪 Jellyseerr", lambda icon, item: open_url("http://localhost:5055")),
    pystray.MenuItem("🟩 Start Jellyseerr", lambda icon, item: os.system(r'start "" "D:\\Scripts\\Jellyserr\\start_jellyserr.vbs"')),
    pystray.MenuItem("🟥 Stop/Shutdown Jellyseerr", lambda icon, item: os.system(r'start "" "D:\\Scripts\\Jellyserr\\stop_jellyserr.vbs"')),
    pystray.MenuItem("🔴 Shutdown PC", lambda icon, item: confirm_shutdown_threaded()),
    pystray.MenuItem("⚫ Quit", quit_program)
)



icon = pystray.Icon("RemoteShutdown", create_icon_image(), "Remote Shutdown", tray_menu)
icon.run()

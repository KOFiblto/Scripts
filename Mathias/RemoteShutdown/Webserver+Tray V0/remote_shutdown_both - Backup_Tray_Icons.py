import threading
import wx
import wx.adv
import webbrowser
from flask import Flask, render_template_string, redirect
import os
import logging
import ctypes
import subprocess

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
@app.errorhandler(Exception)
def handle_exception(e):
    logging.exception("Flask route error:")
    return f"Internal Server Error: {e}", 500

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
    try:
        subprocess.run(["wscript", r"D:\Scripts\jellyseerr\start_jellyseerr.vbs"], check=True)
    except Exception as e:
        logging.exception("Failed to start Jellyseerr")
        return f"Error: {e}", 500
    return "Starting Jellyseerr..."

@app.route("/jellyseerr-stop")
def jellyseerr_stop():
    customprint("Stopping Jellyseerr")
    try:
        subprocess.run(["wscript", r"D:\Scripts\jellyseerr\stop_jellyseerr.vbs"], check=True)
    except Exception as e:
        logging.exception("Failed to stop Jellyseerr")
        return f"Error: {e}", 500
    return "Stopping Jellyseerr..."

@app.route("/shutdown")
def shutdown():
    try:
        os.system("shutdown /s /f /t 0")
        customprint("Shutting down...")
    except Exception as e:
        logging.exception("Shutdown failed")
        return f"Error: {e}", 500
    return "Shutting down..."

@app.route("/status")
def status():
    return "online"

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

# ===== Flask background thread =====
def run_flask():
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000, threads=2)

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# ===== wxPython Tray =====
def load_bitmap(path, size):
    """Load bitmap safely, return placeholder if missing."""
    if not os.path.exists(path):
        logging.warning(f"Icon not found: {path}")
        return wx.Bitmap(size[0], size[1])
    img = wx.Image(path, wx.BITMAP_TYPE_PNG)
    if not img.IsOk():
        logging.warning(f"Failed to load image: {path}")
        return wx.Bitmap(size[0], size[1])
    img = img.Rescale(size[0], size[1], wx.IMAGE_QUALITY_HIGH)
    return wx.Bitmap(img)

class TaskBarIcon(wx.adv.TaskBarIcon):
    ICON_SIZE = (20, 20)

    def __init__(self):
        super().__init__()
        self.set_icon()
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_click)

    def CreatePopupMenu(self):
        menu = wx.Menu()

        items = [
            ("Sonarr", "static/img/sonarr.png", lambda e: webbrowser.open("http://localhost:8989")),
            ("Radarr", "static/img/radarr.png", lambda e: webbrowser.open("http://localhost:7878")),
            ("Jellyfin", "static/img/jellyfin.png", lambda e: webbrowser.open("http://localhost:8096")),
            ("Jellyseerr", "static/img/jellyseerr.png", lambda e: webbrowser.open("http://localhost:5055")),
            ("Start Jellyseerr", "static/img/jellyseerr.png", lambda e: subprocess.run(["wscript", r"D:\Scripts\Jellyseerr\start_jellyseerr.vbs"])),
            ("Stop Jellyseerr", "static/img/jellyseerr.png", lambda e: subprocess.run(["wscript", r"D:\Scripts\Jellyseerr\stop_jellyseerr.vbs"])),
            ("Shutdown PC", "static/img/shutdown.png", self.confirm_shutdown),
            ("Quit", "static/img/quit.png", lambda e: wx.CallAfter(wx.GetApp().Exit))
        ]

        for label, path, handler in items:
            bmp = load_bitmap(path, self.ICON_SIZE)
            item = wx.MenuItem(menu, wx.ID_ANY, label)
            item.SetBitmap(bmp)
            menu.Append(item)
            menu.Bind(wx.EVT_MENU, handler, item)

        return menu

    def set_icon(self):
        bmp = load_bitmap("static/img/tray_icon.png", self.ICON_SIZE)
        icon = wx.Icon()
        icon.CopyFromBitmap(bmp)
        self.SetIcon(icon, "Remote Shutdown")

    def on_left_click(self, event):
        webbrowser.open("http://localhost:5000")

    def confirm_shutdown(self, event):
        result = ctypes.windll.user32.MessageBoxW(None,
            "Are you sure you want to shut down this PC?",
            "Confirm Shutdown", 4)  # Yes/No
        if result == 6:  # Yes
            os.system("shutdown /s /f /t 1")

# ===== Main =====
if __name__ == "__main__":
    wx_app = wx.App(False)
    TaskBarIcon()
    wx_app.MainLoop()
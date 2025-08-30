import logging
import os
import socket
from flask import Flask, render_template_string, redirect, request, render_template

# ===== Logging =====
logging.basicConfig(filename="server.log", level=logging.INFO,
                    format="%(asctime)s %(levelname)s: %(message)s")

app = Flask(__name__)
PRINT = 0

def customprint(text):
    if PRINT:
        print(text)
    logging.info(text)

# ===== Base directory =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JELLYSEER_DIR = r"D:\Scripts\Jellyseerr"

def abs_path(relative_path):
    return os.path.join(BASE_DIR, relative_path)

# ===== Determine local IP =====
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

SERVER_IP = get_local_ip()
PORT_MAPPING = {
    "sonarr": 8989,
    "radarr": 7878,
    "sabnzbd": 6969,
    "jellyfin": 8096,
    "jellyseerr": 5055
}

def redirect_to_service(service_name):
    port = PORT_MAPPING.get(service_name, 5000)
    client_ip = request.remote_addr
    if client_ip == SERVER_IP or client_ip == "127.0.0.1":
        url = f"http://localhost:{port}"
    else:
        url = f"http://{SERVER_IP}:{port}"
    customprint(f"Redirecting {client_ip} -> {url}")
    return redirect(url)

# ===== Routes =====
@app.errorhandler(Exception)
def handle_exception(e):
    logging.exception("Flask route error:")
    return f"Internal Server Error: {e}", 500

@app.route("/sonarr")     
def sonarr():     
    return redirect_to_service("sonarr")
    
@app.route("/radarr")      
def radarr():     
    return redirect_to_service("radarr")
    
@app.route("/sabnzbd")    
def sabnzbd():    
    return redirect_to_service("sabnzbd")
    
@app.route("/jellyfin")   
def jellyfin():   
    return redirect_to_service("jellyfin")
    
@app.route("/jellyseerr") 
def jellyseerr(): 
    return redirect_to_service("jellyseerr")

@app.route("/jellyseerr-start")
def jellyseerr_start():
    customprint("Starting Jellyseerr")
    os.system(f'start "" wscript "{os.path.join(JELLYSEER_DIR, "start_jellyseerr.vbs")}"')
    return "Starting Jellyseerr..."

@app.route("/jellyseerr-stop")
def jellyseerr_stop():
    customprint("Stopping Jellyseerr")
    os.system(f'start "" wscript "{os.path.join(JELLYSEER_DIR, "stop_jellyseerr.vbs")}"')
    return "Stopping Jellyseerr..."

@app.route("/shutdown")
def shutdown():
    os.system("shutdown /s /f /t 0")
    customprint("Shutting down...")
    return "Shutting down..."

@app.route("/status")
def status():
    return "online"

@app.route("/")
def index():
    return render_template("index.html")
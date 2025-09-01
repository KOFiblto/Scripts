import logging
import os
import socket
import psutil
from flask import Flask, render_template_string, redirect, request, render_template, send_from_directory

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
JELLYSEER_DIR = r"D:\Scripts\Mathias\Jellyseerr"

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

# ===== Check if Service is listening on Port (Running/Not running) =====
def is_port_open(port):
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except:
        return False

# ===== Name -> Port =====
SERVER_IP = get_local_ip()
PORT_MAPPING = {
    "sonarr": 8989,
    "radarr": 7878,
    "sabnzbd": 6969,
    "jellyfin": 8096,
    "jellyseerr": 5055,
    "plex": 32400,
    "bazarr": 6767,
    "tdarr": 8265
}

# ===== Redirect to localhost or <Laptop IP> =====
def redirect_to_service(service_name):
    port = PORT_MAPPING.get(service_name, 5000)
    client_ip = request.remote_addr
    if client_ip == SERVER_IP or client_ip == "127.0.0.1":
        url = f"http://localhost:{port}"
    else:
        url = f"http://{SERVER_IP}:{port}"
    customprint(f"Redirecting {client_ip} -> {url}")
    return redirect(url)

# ===== Save Images on Browser =====
@app.after_request
def add_header(response):
    if "static" in request.path:
        response.cache_control.max_age = 60 * 60 * 24 * 30  # 30 days
    return response


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

@app.route("/tdarr")
def tdarr():
    return redirect_to_service("tdarr")

@app.route("/bazarr")      
def bazarr():     
    return redirect_to_service("bazarr")
    
@app.route("/sabnzbd")    
def sabnzbd():    
    return redirect_to_service("sabnzbd")

    
@app.route("/jellyfin")   
def jellyfin():   
    return redirect_to_service("jellyfin")
    
@app.route("/plex")   
def plex():   
    return redirect_to_service("plex")
    
@app.route("/jellyseerr") 
def jellyseerr(): 
    return redirect_to_service("jellyseerr")

@app.route("/jellyseerr-start")
def jellyseerr_start():
    customprint("Starting Jellyseerr")
    os.system(f'start "" wscript "{os.path.join(JELLYSEER_DIR, "start_jellyseerr.vbs")}"')
    return "Starting Jellyseerr... (Takes a while, please be patient!)"

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

@app.route("/service-status")
def service_status():
    status = {}
    for name, port in PORT_MAPPING.items():
        status[name] = is_port_open(port)
    return status

@app.route("/")
def index():
    return render_template("index.html")
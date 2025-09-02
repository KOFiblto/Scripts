import logging
import mimetypes
import os
import socket
import psutil
import hashlib
from threading import Thread
import time
from flask import Flask, render_template_string, redirect, request, render_template, send_from_directory, make_response, jsonify




# =========================================
# =========== F U N C T I O N S ===========
# =========================================

# ===== Rel Path to Abs Path for EXE =====
def abs_path(relative_path):
    return os.path.join(BASE_DIR, relative_path)

# ===== Hash Password Check =====
def check_password(password):
    return hashlib.sha256(password.encode()).hexdigest() == PASSWORD_HASH

# ===== Log =====
def customprint(text):
    if PRINT:
        print(text)
    logging.info(text)

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
    sock = socket.socket()
    sock.settimeout(0.1)
    try:
        sock.connect(("127.0.0.1", port))
        return True
    except:
        return False
    finally:
        sock.close()

# ===== Update Service Status =====
def update_status_cache():
    global status_cache
    while True:
        status_cache = {name: is_port_open(port) for name, port in PORT_MAPPING.items()}
        time.sleep(5)


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



# =========================================
# =========== V A R I A B L E S ===========
# =========================================

# ===== Variables =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JELLYSEER_DIR = r"D:\Scripts\Mathias\Jellyseerr"
PASSWORD_HASH = "551cd4a09edfca75f017fedf4b4aefabd127d91072de3c3a1d2b6ffc511f8fa8"
SERVER_IP = get_local_ip()
status_cache = {}
PRINT = 0
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
# ===== FLASK / THREADING =====
status_thread = Thread(target=update_status_cache, daemon=True)
status_thread.start()
app = Flask(__name__)

# ===== Allow WEBP =====
mimetypes.add_type('image/webp', '.webp')

# ===== Logging =====
logging.basicConfig(filename="server.log", level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")




# =========================================
# ============== R O U T E S ==============
# =========================================

# ===== Error =====
@app.errorhandler(Exception)
def handle_exception(e):
    logging.exception("Flask route error:")
    return f"Internal Server Error: {e}", 500


# ===== Save Images on Browser =====
@app.after_request
def add_header(response):
    if "static" in request.path:
        response.cache_control.max_age = 60 * 60 * 24 * 30  # 30 days
    return response


# ===== Sonarr =====
@app.route("/sonarr")     
def sonarr():     
    return redirect_to_service("sonarr")
    

# ===== Radarr =====
@app.route("/radarr")       
def radarr():     
    return redirect_to_service("radarr")


# ===== Tdarr =====
@app.route("/tdarr")
def tdarr():
    return redirect_to_service("tdarr")


# ===== Bazarr =====
@app.route("/bazarr")      
def bazarr():     
    return redirect_to_service("bazarr")
    

# ===== SABnzbd =====
@app.route("/sabnzbd")    
def sabnzbd():    
    return redirect_to_service("sabnzbd")


# ===== Jellyfin =====
@app.route("/jellyfin")   
def jellyfin():   
    return redirect_to_service("jellyfin")
    

# ===== Plex =====
@app.route("/plex")   
def plex():   
    return redirect_to_service("plex")
    

# ===== Jellyseerr =====
@app.route("/jellyseerr") 
def jellyseerr(): 
    return redirect_to_service("jellyseerr")


# ===== Jellyseerr Start =====
@app.route("/jellyseerr-start", methods=['POST'])
def jellyseerr_start():
    data = request.get_json()
    if not data or 'password' not in data:
        return "No password provided!", 400

    if not check_password(data['password']):
        return "Incorrect password! Start aborted.", 403

    customprint("Starting Jellyseerr")
    os.system(f'start "" wscript "{os.path.join(JELLYSEER_DIR, "start_jellyseerr.vbs")}"')
    return "Starting Jellyseerr... (Takes a while, please be patient!)"


# ===== Jellyseerr Stop =====
@app.route("/jellyseerr-stop", methods=['POST'])
def jellyseerr_stop():
    data = request.get_json()
    if not data or 'password' not in data:
        return "No password provided!", 400

    if not check_password(data['password']):
        return "Incorrect password! Stop aborted.", 403

    customprint("Stopping Jellyseerr")
    os.system(f'start "" wscript "{os.path.join(JELLYSEER_DIR, "stop_jellyseerr.vbs")}"')
    return "Stopping Jellyseerr..."


# ===== Shutdown PC =====
@app.route('/shutdown', methods=['POST'])
def shutdown():
    data = request.get_json()
    if not data or 'password' not in data:
        return "No password provided!", 400

    password = data['password']
    if not check_password(password):
        return "Incorrect password! Shutdown aborted.", 403
   
    os.system("shutdown /s /f /t 0")
    return "Shutting down..."


# ===== Status Dots =====
@app.route("/service-status")
def service_status():
    return jsonify(status_cache)


# ===== Home =====
@app.route("/")
def index():
    return render_template("index.html")


# ===== Load WEBP images =====
@app.route("/img/<filename>")
def serve_img(filename):
    path = os.path.join(app.root_path, "static/img")
    response = make_response(send_from_directory(path, filename))

    response.headers["Cache-Control"] = "public, max-age=604800" # 604800 sec = 1 Week
    return response
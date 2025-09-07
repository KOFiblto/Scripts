import logging
import mimetypes
import os
import psutil # type: ignore
import socket
import hashlib
from threading import Thread
import time
import subprocess
from flask import Flask, render_template_string, redirect, request, render_template, send_from_directory, make_response, jsonify # type: ignore




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

def is_local_request():
    return request.remote_addr in ("127.0.0.1", "::1", "localhost", get_local_ip())


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

def is_service_running(service):
    action = SERVICES.get(service)
    if not action:
        return False

    if action["type"] == "exe":
        name = os.path.basename(action["start"])
        for proc in psutil.process_iter(["name"]):
            if proc.info["name"] == name:
                return True
        return False
    else:
        return is_port_open(action.get("port", 0))


# ===== Update Service Status =====
def update_status_cache():
    global status_cache
    while True:
        new_status = {}
        for name, info in SERVICES.items():
            port_open = is_port_open(info["port"])
            service_running = is_service_running(name)
            if name == "plex": # Special for Plex, as it keeps the port open for some reason
                new_status[name] = port_open and service_running
            else:
                new_status[name] = port_open or service_running
        status_cache = new_status
        time.sleep(1)



# ===== Redirect to localhost or <Laptop IP> =====
def redirect_to_service(service_name):
    port = SERVICES[service_name].get("port", 5000)
    client_ip = request.remote_addr
    if client_ip == SERVER_IP or client_ip == "127.0.0.1":
        url = f"http://localhost:{port}"
    else:
        url = f"http://{SERVER_IP}:{port}"
    customprint(f"Redirecting {client_ip} -> {url}")
    return redirect(url)


# ===== Start a Service =====
def start_service(service):
    action = SERVICES.get(service)
    if not action:
        return f"Unknown service '{service}'", 404

    try:
        if action["type"] == "exe":
            subprocess.Popen(
                action["start"],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )
        elif action["type"] == "taskkill":
            subprocess.Popen(action["start"], shell=True)
        elif action["type"] == "service":
            subprocess.run(["sc", "start", action["name"]], shell=True)
        elif action["type"] == "vbs":
            subprocess.Popen(
                ["wscript", action["start"]],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )
    except Exception as e:
        logging.exception(f"Failed to start {service}:")
        return f"Error starting {service}: {e}", 500

    return f"Starting {service}..."


# ===== Stop a Service =====
def stop_service(service):
    action = SERVICES.get(service)
    if not action:
        return f"Unknown service '{service}'", 404

    try:
        if action["type"] == "exe" or action["type"] == "taskkill":
            subprocess.run(action["stop"], shell=True)
        elif action["type"] == "service":
            subprocess.run(["sc", "stop", action["name"]], shell=True)
        elif action["type"] == "vbs":
            subprocess.Popen(
                ["wscript", action["stop"]],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )
    except Exception as e:
        logging.exception(f"Failed to stop {service}:")
        return f"Error stopping {service}: {e}", 500

    return f"Stopping {service}..."



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

SERVICES = {
    "sonarr": {
        "port": 8989,
        "type": "exe",
        "start": r"C:\ProgramData\Sonarr\bin\Sonarr.exe",
        "stop": "taskkill /IM Sonarr.exe /F"
    },
    "radarr": {
        "port": 7878,
        "type": "exe",
        "start": r"C:\ProgramData\Radarr\bin\Radarr.exe",
        "stop": "taskkill /IM Radarr.exe /F"
    },
    "sabnzbd": {
        "port": 6969,
        "type": "exe",
        "start": r"C:\Program Files\SABnzbd\SABnzbd.exe",
        "stop": "taskkill /IM SABnzbd.exe /F"
    },
    "jellyfin": {
        "port": 8096,
        "type": "exe",
        "start": r"C:\Program Files\Jellyfin\Server\jellyfin.exe",
        "stop": "taskkill /IM jellyfin.exe /F"
    },
    "plex": {
        "port": 32400,
        "type": "exe",
        "start": r"C:\Program Files\Plex\Plex Media Server\Plex Media Server.exe",
        "stop": "taskkill /IM \"Plex Media Server.exe\" /F"
    },
    "bazarr": {
        "port": 6767,
        "type": "service",
        "name": "Bazarr"
        # CMD to give Access to User:
        # sc sdset Bazarr "D:(A;;RPWP;;;BU)(A;;CCLCSWRPWPDTLOCRRC;;;SY)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)(A;;CCLCSWLOCRRC;;;IU)(A;;CCLCSWLOCRRC;;;SU)S:(AU;FA;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;WD)"
    },
    "tdarr": {
        "port": 8265,
        "type": "service",
        "name": "TdarrServer"
        # CMD to give Acces to User
        # sc sdset TdarrServer "D:(A;;RPWP;;;BU)(A;;CCLCSWRPWPDTLOCRRC;;;SY)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)(A;;CCLCSWLOCRRC;;;IU)(A;;CCLCSWLOCRRC;;;SU)S:(AU;FA;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;WD)"
    },
    "jellyseerr": {
        "port": 5055,
        "type": "vbs",
        "start": os.path.join(JELLYSEER_DIR, "start_jellyseerr.vbs"),
        "stop": os.path.join(JELLYSEER_DIR, "stop_jellyseerr.vbs")
    },
}


# ===== FLASK / THREADING =====
status_thread = Thread(target=update_status_cache, daemon=True)
status_thread.start()
app = Flask(__name__)

# ===== Add WEBP to flask =====
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


# ===== Validate Images on local Browser =====
@app.after_request
def add_header(response):
    if "static" in request.path:
        response.cache_control.max_age = 60 * 60 * 24 * 30  # 30 days
    return response


# ===== Universal Router for Services =====
@app.route("/<service>")
def universal_router(service):
    if service in SERVICES:
        return redirect_to_service(service)
    return f"Service '{service}' not found", 404


# ===== Start Service =====
@app.route("/start/<service>", methods=["POST"])
def start(service):
    if not is_local_request():
        data = request.get_json()
        if not data or 'password' not in data or not check_password(data['password']):
            return "Unauthorized: invalid password", 403
    return start_service(service)


# ===== Stop service =====
@app.route("/stop/<service>", methods=["POST"])
def stop(service):
    if not is_local_request():
        data = request.get_json()
        if not data or 'password' not in data or not check_password(data['password']):
            return "Unauthorized: invalid password", 403
    return stop_service(service)


# ===== Shutdown =====
@app.route('/shutdown', methods=['POST'])
def shutdown():
    if not is_local_request():
        data = request.get_json()
        if not data or 'password' not in data or not check_password(data['password']):
            return "Unauthorized: invalid password", 403
    os.system("shutdown /s /f /t 0")  # uncomment when ready
    return "Shutting down..."


# ===== Status Dots =====
@app.route("/service-status")
def service_status():
    return jsonify(status_cache)


@app.route("/verify-password", methods=["POST"])
def verify_password():
    if is_local_request():
        return "OK", 200
    else:
        data = request.get_json()
        if not data or 'password' not in data:
            return "No password provided!", 400
        if not check_password(data['password']):
            return "Incorrect password", 403
        return "OK", 200


# ===== Home =====
@app.route("/")
def index():
    return render_template("index.html")


# ===== Load WEBP images =====
@app.route("/img/<filename>")
def serve_img(filename):
    path = os.path.join(app.root_path, "static/img/webp")
    response = make_response(send_from_directory(path, filename))

    response.headers["Cache-Control"] = "public, max-age=604800" # 604800 sec = 1 Week
    return response
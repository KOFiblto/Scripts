import logging
import mimetypes
import os
import psutil # type: ignore
import socket
import hashlib
from threading import Thread
import time
import subprocess
import platform
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
    container = action["container"]
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", container],
            capture_output=True, text=True, timeout=3, creationflags=subprocess.CREATE_NO_WINDOW
        )
        return result.stdout.strip() == "true"
    except subprocess.TimeoutExpired:
        print(f"Docker call timed out for {container}")
        return False
    except Exception as e:
        print(f"Error checking service {container}: {e}")
        return False



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


# ===== Run Docker Command =====
def run_docker_command(command_args):
    """Run docker command via PowerShell with hidden window"""
    full_command = ["powershell", "-WindowStyle", "Hidden"] + command_args
    
    try:
        result = subprocess.run(
            full_command,
            capture_output=True, 
            text=True, 
            check=True
        )
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"Docker command failed: {e.stderr.strip()}")
        raise


# ===== Start a Service =====
def start_service(service):
    action = SERVICES.get(service)
    if not action:
        return f"Unknown service '{service}'", 404

    container = action["container"]
    try:
        result = run_docker_command(["docker", "start", container])
        logging.info(f"Started {container}: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to start {container}: {e.stderr.strip()}")


# ===== Stop a Service =====
def stop_service(service):
    action = SERVICES.get(service)
    if not action:
        return f"Unknown service '{service}'", 404

    container = action["container"]
    try:
        result = run_docker_command(["docker", "stop", container])
        logging.info(f"Stopped {container}: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to stop {container}: {e.stderr.strip()}")



# =========================================
# =========== V A R I A B L E S ===========
# =========================================

# ===== Variables =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PASSWORD_HASH = "551cd4a09edfca75f017fedf4b4aefabd127d91072de3c3a1d2b6ffc511f8fa8"
SERVER_IP = get_local_ip()
status_cache = {}
PRINT = 0

SERVICES = {
    "sonarr":  {"container": "sonarr", "port": 9005},
    "radarr":  {"container": "radarr", "port": 9004},
    "sabnzbd": {"container": "sabnzbd", "port": 9006},
    "jellyfin": {"container": "jellyfin", "port": 9001},
    "plex": {"container": "plex", "port": 9002},
    "bazarr": {"container": "bazarr", "port": 9003},
    "tdarr": {"container": "tdarr", "port": 9007},
    "whisparr": {"container": "whisparr", "port": 9008},
}


# ===== Debugg =====
print("Starting status thread...")
logging.basicConfig(filename="service_debug.log", level=logging.DEBUG)
logging.debug("Script started")
try:
    subprocess.run(["docker", "info"], capture_output=True, timeout=2, creationflags=subprocess.CREATE_NO_WINDOW)
except Exception as e:
    print("Docker not running:", e)

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


# ===== Start all services =====
@app.route("/start-all", methods=["POST"])
def start_all():
    if not is_local_request():
        data = request.get_json()
        if not data or 'password' not in data or not check_password(data['password']):
            return "Unauthorized: invalid password", 403

    results = {}
    for service in SERVICES:
        if is_service_running(service):
            results[service] = f"{service} already running"
        else:
            msg = start_service(service)
            results[service] = msg if isinstance(msg, str) else str(msg)
    return jsonify(results)


# ===== Stop all services =====
@app.route("/stop-all", methods=["POST"])
def stop_all():
    if not is_local_request():
        data = request.get_json()
        if not data or 'password' not in data or not check_password(data['password']):
            return "Unauthorized: invalid password", 403

    results = {}
    for service in SERVICES:
        if not is_service_running(service):
            results[service] = f"{service} already stopped"
        else:
            msg = stop_service(service)
            results[service] = msg if isinstance(msg, str) else str(msg)
    return jsonify(results)


# ===== Shutdown =====
@app.route('/shutdown', methods=['POST'])
def shutdown():
    if not is_local_request():
        data = request.get_json()
        if not data or 'password' not in data or not check_password(data['password']):
            return "Unauthorized: invalid password", 403
    os.system("shutdown /s /f /t 0") 
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
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import docker
import os
from config import SERVICES, SERVER_IP

# Set static folder to ../client
app = Flask(__name__, static_folder='../client')
CORS(app)

try:
    client = docker.from_env()
    client.ping()
except Exception:
    try:
        # Try explicit Windows pipe
        client = docker.DockerClient(base_url='npipe:////./pipe/docker_engine')
        client.ping()
    except Exception as e:
        print(f"Error connecting to Docker: {e}")
        client = None

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/services', methods=['GET'])
def get_services():
    services_status = []
    for service in SERVICES:
        status = "stopped"
        if client:
            try:
                container = client.containers.get(service["container_name"])
                status = container.status
            except docker.errors.NotFound:
                status = "not_found"
            except Exception as e:
                print(f"Error getting status for {service['name']}: {e}")
                status = "error"
        
        services_status.append({
            **service,
            "status": status,
            "server_ip": SERVER_IP
        })
    return jsonify(services_status)

@app.route('/api/services/<service_id>/start', methods=['POST'])
def start_service(service_id):
    if not client:
        return jsonify({"error": "Docker not available"}), 500
        
    service = next((s for s in SERVICES if s["id"] == service_id), None)
    if not service:
        return jsonify({"error": "Service not found"}), 404

    try:
        container = client.containers.get(service["container_name"])
        container.start()
        return jsonify({"message": f"Started {service['name']}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/services/<service_id>/stop', methods=['POST'])
def stop_service(service_id):
    if not client:
        return jsonify({"error": "Docker not available"}), 500

    service = next((s for s in SERVICES if s["id"] == service_id), None)
    if not service:
        return jsonify({"error": "Service not found"}), 404

    try:
        container = client.containers.get(service["container_name"])
        container.stop()
        return jsonify({"message": f"Stopped {service['name']}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

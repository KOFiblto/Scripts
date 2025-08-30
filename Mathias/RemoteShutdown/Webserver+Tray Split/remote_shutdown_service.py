from waitress import serve
from remote_shutdown_flask import app

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=5000, threads=2)

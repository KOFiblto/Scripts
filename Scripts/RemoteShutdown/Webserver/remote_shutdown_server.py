from flask import Flask, render_template_string, redirect, url_for
import os

app = Flask(__name__)

PRINT = 0

def customprint(text):
    if PRINT == 1:
        print(text)

# === Routes for shortcuts ===
@app.route("/sabnzbd")
def sabnzbd():
    customprint("sabnzbd redirect")
    return redirect("http://192.168.178.21:6969")

@app.route("/jellyfin")
def jellyfin():
    customprint("jellyfin redirect")
    return redirect("http://192.168.178.21:8096")

@app.route("/sonarr")
def sonarr():
    customprint("sonarr redirect")
    return redirect("http://192.168.178.21:8989")

@app.route("/radarr")
def radarr():
    customprint("radarr redirect")
    return redirect("http://192.168.178.21:7878")

# === Shutdown endpoint ===
@app.route("/shutdown", methods=["GET", "POST"])
def shutdown():
    os.system("shutdown /s /t 0")
    customprint("Shutting down")
    return "Shutting down..."

# === Status endpoint ===
@app.route("/status")
def status():
    return "online"

# === Homepage with buttons ===
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
            .btn {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 90%;
                max-width: 500px;
                margin: 1rem 0;
                padding: 1rem;
                font-size: 2rem;
                min-height: 6vh;
                max-height: 10vh;
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
            .btn:hover {
                background: #0056b3;
            }
            .btn-danger {
                background: #dc3545;
            }
            .btn-danger:hover {
                background: #a71d2a;
            }
            /* Status box */
            #status-box {
                margin-top: 1rem;
                padding: 1rem 2rem;
                border-radius: 1rem;
                font-size: 2.5rem;
                font-weight: bold;
                color: white;
                min-width: 250px;
            }
            /* Mobile / small screens */
            @media (max-width: 1000px) {
                .btn {
                    font-size: 3rem;
                    min-height: 8vh;
                    max-height: 15vh;
                    padding: 1rem;
                    flex-direction: row;
                }
                .btn img {
                    max-height: 4rem;
                    margin-right: 1rem;
                }
                h1 {
                    font-size: 2.5rem;
                }
                #status-box {
                    font-size: 3rem;
                }
            }
        </style>
    </head>
    <body>
        <h1>Mathias Laptop</h1>
        <a class="btn" href="/sonarr">
            <img src="{{ url_for('static', filename='img/sonarr.png') }}" alt="Sonarr"> Sonarr
        </a>
        <a class="btn" href="/radarr">
            <img src="{{ url_for('static', filename='img/radarr.png') }}" alt="Radarr"> Radarr
        </a>
        <a class="btn" href="/sabnzbd">
            <img src="{{ url_for('static', filename='img/sabnzbd.png') }}" alt="SABnzbd"> SABnzbd
        </a>
        <a class="btn" href="/jellyfin">
            <img src="{{ url_for('static', filename='img/jellyfin.png') }}" alt="Jellyfin"> Jellyfin
        </a>
        <a class="btn btn-danger" href="javascript:void(0);" onclick="shutdown()">
            <img src="{{ url_for('static', filename='img/shutdown.png') }}" alt="Shutdown"> Shutdown
        </a>

        <div id="status-box">Loading... <span id="flash-dot">•</span></div>

        <script>
            const statusBox = document.getElementById("status-box");
            const flashDot = document.getElementById("flash-dot");
            let statusInterval = null;

            function flash() {
                flashDot.style.opacity = "1";
                setTimeout(() => {
                    flashDot.style.opacity = "0";
                }, 200);
            }

            function checkStatus() {
                fetch('/status', {cache: "no-store"})
                    .then(response => response.text())
                    .then(data => {
                        statusBox.innerText = "Online";
                        statusBox.appendChild(flashDot); // ensure dot stays in box
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
                clearInterval(statusInterval);
                statusBox.innerText = "Shutting down...";
                statusBox.appendChild(flashDot);
                statusBox.style.backgroundColor = "orange";

                setTimeout(() => {
                    statusInterval = setInterval(checkStatus, 1000);
                }, 3000);

                fetch('/shutdown')
                    .then(response => response.text())
                    .then(data => console.log(data))
                    .catch(error => console.log(error));
            }

            // Start polling every second
            statusInterval = setInterval(checkStatus, 1000);

            // Initial flash-dot style
            flashDot.style.transition = "opacity 0.1s";
            flashDot.style.opacity = "0";
        </script>

    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

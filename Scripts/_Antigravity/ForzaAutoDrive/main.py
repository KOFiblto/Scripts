import os
import sys
import webbrowser
import threading
import shutil
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse

# Local imports
import db
import autodrive

app = FastAPI(title="Forza Horizon AutoDrive Web API")

# Ensure required workspaces exist
os.makedirs("static", exist_ok=True)
os.makedirs("static/images", exist_ok=True)

# Mount static files folder
app.mount("/static", StaticFiles(directory="static"), name="static")

# Shared thread-safe status tracker & controller runner
tracker = autodrive.StatusTracker()
runner = autodrive.AutodriveRunner(tracker)

@app.get("/")
def read_root():
    # Redirect root to webapp front page
    return RedirectResponse(url="/static/index.html")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse("static/favicon.png")

# Tracks CRUD endpoints
@app.get("/api/tracks")
def get_tracks():
    return db.get_all_tracks()

@app.post("/api/tracks")
def add_track(data: dict):
    name = data.get("name")
    ttype = data.get("type", "Race")
    if not name:
        raise HTTPException(status_code=400, detail="Name required")
    track_id = db.add_track(name, ttype)
    if not track_id:
        raise HTTPException(status_code=400, detail="Track name already exists")
    return {"id": track_id}

@app.put("/api/tracks/{track_id}")
def update_track(track_id: int, data: dict):
    name = data.get("name")
    ttype = data.get("type")
    image_path = data.get("image_path", "")
    db.update_track(track_id, name, ttype, image_path)
    return {"status": "ok"}

@app.delete("/api/tracks/{track_id}")
def delete_track(track_id: int):
    db.delete_track(track_id)
    return {"status": "ok"}

# Cars CRUD endpoints
@app.get("/api/tracks/{track_id}/cars")
def get_cars(track_id: int):
    return db.get_cars_by_track(track_id)

@app.post("/api/cars")
def add_car_to_track_endpoint(data: dict):
    track_id = data.get("track_id")
    global_car_id = data.get("global_car_id")
    if not track_id or not global_car_id:
        raise HTTPException(status_code=400, detail="track_id and global_car_id required")
    setup_id = db.add_car_to_track(track_id, global_car_id)
    if not setup_id:
        raise HTTPException(status_code=400, detail="Car already added to this track")
    return {"id": setup_id}

@app.put("/api/cars/{car_id}")
def update_car(car_id: int, data: dict):
    db.update_car(
        car_setup_id=car_id,
        time_seconds=float(data.get("time_seconds", 60.0)),
        xp=int(data.get("xp", 0)),
        cr=int(data.get("cr", 0)),
        cr_multiplier=float(data.get("cr_multiplier", 0.0)),
        skillpoints=int(data.get("skillpoints", 0)),
        drift_interval=float(data.get("drift_interval")) if data.get("drift_interval") is not None else None,
        drift_duration=float(data.get("drift_duration")) if data.get("drift_duration") is not None else None,
        drift_button=data.get("drift_button")
    )
    return {"status": "ok"}

@app.delete("/api/cars/{car_id}")
def delete_car(car_id: int):
    db.delete_car(car_id)
    return {"status": "ok"}

@app.post("/api/cars/{car_id}/image")
async def upload_car_image(car_id: int, file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1]
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT global_car_id FROM cars WHERE id=?", (car_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Setup not found")
    global_car_id = row[0]
    
    filename = f"car_{global_car_id}{ext}"
    dest_path = os.path.join("static", "images", filename)
    
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    web_path = f"/static/images/{filename}"
    db.update_global_car_image_by_setup(car_id, web_path)
    return {"image_path": web_path}

# Global Cars CRUD endpoints
@app.get("/api/global-cars")
def get_global_cars():
    return db.get_all_global_cars()

@app.post("/api/global-cars")
def add_global_car(data: dict):
    name = data.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Name required")
    car_id = db.add_global_car(name)
    if not car_id:
        raise HTTPException(status_code=400, detail="Car name already exists")
    return {"id": car_id}

@app.put("/api/global-cars/{car_id}")
def update_global_car(car_id: int, data: dict):
    name = data.get("name")
    image_path = data.get("image_path", "")
    db.update_global_car(car_id, name, image_path)
    return {"status": "ok"}

@app.delete("/api/global-cars/{car_id}")
def delete_global_car(car_id: int):
    db.delete_global_car(car_id)
    return {"status": "ok"}

@app.post("/api/global-cars/{car_id}/image")
async def upload_global_car_image(car_id: int, file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1]
    filename = f"car_{car_id}{ext}"
    dest_path = os.path.join("static", "images", filename)
    
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    web_path = f"/static/images/{filename}"
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM global_cars WHERE id=?", (car_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        db.update_global_car(car_id, row[0], web_path)
    return {"image_path": web_path}

@app.post("/api/tracks/{track_id}/image")
async def upload_track_image(track_id: int, file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1]
    filename = f"track_{track_id}{ext}"
    dest_path = os.path.join("static", "images", filename)
    
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    web_path = f"/static/images/{filename}"
    
    tracks = db.get_all_tracks()
    track = next((t for t in tracks if t["id"] == track_id), None)
    if track:
        db.update_track(track_id, track["name"], track["type"], web_path)
    return {"image_path": web_path}

# Settings endpoints
@app.get("/api/settings")
def get_settings():
    return db.get_settings()

@app.get("/api/rankings")
def get_rankings():
    return db.get_all_cars()

@app.post("/api/settings")
def save_settings(data: dict):
    for k, v in data.items():
        db.save_setting(k, v)
    return {"status": "ok"}

# Sequences endpoints
@app.get("/api/sequences/{name}")
def get_sequence(name: str):
    return db.get_sequence_steps(name)

@app.post("/api/sequences/{name}")
def save_sequence(name: str, data: list):
    db.save_sequence_steps(name, data)
    return {"status": "ok"}

# Driving Runner endpoints
@app.post("/api/drive/start")
def start_drive(data: dict):
    track_id = data.get("track_id")
    car_id = data.get("car_id")
    
    tracks = db.get_all_tracks()
    track = next((t for t in tracks if t["id"] == track_id), None)
    if not track:
        raise HTTPException(status_code=400, detail="Track profile not found")
        
    cars_list = db.get_cars_by_track(track_id)
    car = next((c for c in cars_list if c["id"] == car_id), None)
    if not car:
        raise HTTPException(status_code=400, detail="Car profile not found")
        
    start_steps = db.get_sequence_steps("universal_start")
    post_steps = db.get_sequence_steps("post_race")
    
    # Merge overrides from checklist console options
    settings_dict = db.get_settings()
    settings_dict["execution_focus_mode"] = data.get("focus_mode", "Foreground")
    settings_dict["execution_auto_enable"] = "True" if data.get("auto_enable_autodrive", True) else "False"
    
    # Check running lock
    if tracker.get_snapshot()["is_running"]:
        raise HTTPException(status_code=400, detail="AutoDrive runner is already active")
        
    # Start background execution thread
    runner.start(track, car, start_steps, post_steps, settings_dict)
    return {"status": "ok"}

@app.post("/api/drive/stop")
def stop_drive():
    runner.stop()
    return {"status": "ok"}

@app.get("/api/drive/status")
def get_drive_status():
    return tracker.get_snapshot()

def open_browser():
    webbrowser.open("http://127.0.0.1:8900")

if __name__ == "__main__":
    db.init_db()
    # Auto launch client web page
    threading.Timer(1.2, open_browser).start()
    uvicorn.run("main:app", host="127.0.0.1", port=8900, reload=False)

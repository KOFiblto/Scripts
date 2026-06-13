import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "forza_autodrive.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if global_cars already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='global_cars'")
    has_global_cars = cursor.fetchone() is not None
    
    if not has_global_cars:
        # We need to transition the database!
        # Let's read old cars if the old cars table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cars'")
        has_old_cars = cursor.fetchone() is not None
        
        old_cars = []
        old_tracks = []
        old_sequences = []
        old_settings = []
        
        if has_old_cars:
            try:
                cursor.execute("SELECT * FROM cars")
                old_cars = [dict(r) for r in cursor.fetchall()]
            except Exception:
                pass
            try:
                cursor.execute("SELECT * FROM tracks")
                old_tracks = [dict(r) for r in cursor.fetchall()]
            except Exception:
                pass
            try:
                cursor.execute("SELECT * FROM sequences")
                old_sequences = [dict(r) for r in cursor.fetchall()]
            except Exception:
                pass
            try:
                cursor.execute("SELECT * FROM settings")
                old_settings = [dict(r) for r in cursor.fetchall()]
            except Exception:
                pass
            
            # Drop old tables
            cursor.execute("DROP TABLE IF EXISTS cars")
            cursor.execute("DROP TABLE IF EXISTS tracks")
            cursor.execute("DROP TABLE IF EXISTS sequences")
            cursor.execute("DROP TABLE IF EXISTS settings")
            conn.commit()
            
        # Recreate tables
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            type TEXT, -- 'Race', 'Time Attack', 'Drift'
            image_path TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS global_cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            image_path TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER,
            global_car_id INTEGER,
            time_seconds REAL,
            xp INTEGER,
            cr INTEGER,
            cr_multiplier REAL DEFAULT 0.0,
            skillpoints INTEGER,
            drift_interval REAL,
            drift_duration REAL,
            drift_button TEXT,
            FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
            FOREIGN KEY (global_car_id) REFERENCES global_cars(id) ON DELETE CASCADE,
            UNIQUE(track_id, global_car_id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sequences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sequence_name TEXT, -- 'universal_start', 'post_race'
            step_index INTEGER,
            label TEXT,
            action_type TEXT,
            action_value TEXT,
            delay REAL,
            repetitions INTEGER
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            track_id INTEGER,
            car_setup_id INTEGER,
            cr INTEGER,
            xp INTEGER,
            skillpoints INTEGER,
            FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
            FOREIGN KEY (car_setup_id) REFERENCES cars(id) ON DELETE CASCADE
        )
        """)
        conn.commit()
        
        # Restore or Seed Settings
        if old_settings:
            for s in old_settings:
                cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (s["key"], s["value"]))
        else:
            default_settings = [
                ("focus_window_enabled", "True"),
                ("startup_delay", "5"),
                ("autodrive_activation_enabled", "True"),
                ("autodrive_activation_delay", "5.0"),
                ("video_runs_to_keep", "2"),
                ("control_ACCELERATE", "RT"),
                ("control_BRAKE", "LT"),
                ("control_EBRAKE", "A_BTN"),
                ("control_ACTIVATE", "A_BTN"),
                ("control_START_EVENT", "X_BTN"),
                ("control_ANNA", "DPAD_DOWN"),
                ("control_AUTODRIVE", "DPAD_LEFT")
            ]
            cursor.executemany("INSERT INTO settings (key, value) VALUES (?, ?)", default_settings)
            
        # Restore or Seed Sequences
        if old_sequences:
            for seq in old_sequences:
                cursor.execute("""
                INSERT INTO sequences (sequence_name, step_index, label, action_type, action_value, delay, repetitions)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (seq["sequence_name"], seq["step_index"], seq["label"], seq["action_type"], seq["action_value"], seq["delay"], seq["repetitions"]))
        else:
            # Universal Start Sequence
            start_steps = [
                ("universal_start", 1, "Start Event (X)", "button", "ROLE_START_EVENT", 3.0, 1),
                ("universal_start", 2, "Go to Custom - Flick Down", "stick", "STICK_DOWN", 0.0, 1),
                ("universal_start", 3, "Go to Custom - Press A", "button", "ROLE_ACTIVATE", 3.0, 1),
                ("universal_start", 4, "Change Cars - Flick Up", "stick", "STICK_UP", 0.0, 1),
                ("universal_start", 5, "Change Cars - Press A", "button", "ROLE_ACTIVATE", 3.0, 1),
                ("universal_start", 6, "Select All Cars - Left 20x", "stick", "STICK_LEFT", 0.0, 20),
                ("universal_start", 7, "Select All Cars - Flick Up", "stick", "STICK_UP", 0.0, 1),
                ("universal_start", 8, "Select All Cars - Press A", "button", "ROLE_ACTIVATE", 4.0, 1),
                ("universal_start", 9, "Select X-Class", "button", "ROLE_ACTIVATE", 2.0, 1),
                ("universal_start", 10, "Confirm Event - Flick Down", "stick", "STICK_DOWN", 0.0, 1),
                ("universal_start", 11, "Confirm Event - Press A", "button", "ROLE_ACTIVATE", 2.0, 1),
                ("universal_start", 12, "Start with Solo", "button", "ROLE_ACTIVATE", 2.0, 1),
                ("universal_start", 13, "Keep current Car / Loading Menu", "button", "ROLE_ACTIVATE", 30.0, 1),
                ("universal_start", 14, "Dismiss potential difficulty prompts", "button", "B_BTN", 1.0, 1),
                ("universal_start", 15, "Start race", "button", "ROLE_ACTIVATE", 0.0, 1)
            ]
            post_steps = [
                ("post_race", 1, "Out of Leaderboard / Leaving Race", "button", "ROLE_ACTIVATE", 30.0, 1)
            ]
            cursor.executemany("INSERT INTO sequences (sequence_name, step_index, label, action_type, action_value, delay, repetitions) VALUES (?, ?, ?, ?, ?, ?, ?)", start_steps + post_steps)
            
        # Restore or Seed Tracks and Migrate/Seed Cars
        if old_tracks:
            for t in old_tracks:
                cursor.execute("INSERT OR REPLACE INTO tracks (id, name, type, image_path) VALUES (?, ?, ?, ?)", (t["id"], t["name"], t["type"], t.get("image_path", "")))
        else:
            tracks_data = [
                ("The Colossus", "Race", ""),
                ("Hokubu", "Time Attack", ""),
                ("Soni", "Time Attack", ""),
                ("Sekibe", "Time Attack", ""),
                ("Horizon Time Attack Template", "Time Attack", ""),
                ("Horizon Drift Loop", "Drift", "")
            ]
            cursor.executemany("INSERT INTO tracks (name, type, image_path) VALUES (?, ?, ?)", tracks_data)
            
        conn.commit()
        
        # Get track IDs map
        cursor.execute("SELECT id, name FROM tracks")
        track_map = {row["name"]: row["id"] for row in cursor.fetchall()}
        
        # Populate global cars and map them to track setup entries
        if old_cars:
            for car in old_cars:
                # Insert global car if not exists
                cursor.execute("INSERT OR IGNORE INTO global_cars (name, image_path) VALUES (?, ?)", (car["name"], car.get("image_path", "")))
                cursor.execute("SELECT id FROM global_cars WHERE name=?", (car["name"],))
                g_car_id = cursor.fetchone()[0]
                
                # Insert setup
                cursor.execute("""
                INSERT OR IGNORE INTO cars (track_id, global_car_id, time_seconds, xp, cr, skillpoints, drift_interval, drift_duration, drift_button)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (car["track_id"], g_car_id, car["time_seconds"], car["xp"], car["cr"], car["skillpoints"], car.get("drift_interval"), car.get("drift_duration"), car.get("drift_button")))
        else:
            # Seed default global cars
            g_cars_seed = [
                ("Lotus Evija", ""),
                ("Ford", ""),
                ("BMW M4", ""),
                ("Template Car", ""),
                ("BMW M4 Drift", "")
            ]
            cursor.executemany("INSERT OR IGNORE INTO global_cars (name, image_path) VALUES (?, ?)", g_cars_seed)
            conn.commit()
            
            # Get global car IDs map
            cursor.execute("SELECT id, name FROM global_cars")
            g_car_map = {row["name"]: row["id"] for row in cursor.fetchall()}
            
            # Seed default track car setups
            cars_data = [
                # Track: The Colossus
                (track_map["The Colossus"], g_car_map["Lotus Evija"], 325.0, 17950, 140000, 150000, None, None, None),
                (track_map["The Colossus"], g_car_map["Ford"], 380.0, 8700, 160000, 50000, None, None, None),
                # Track: Hokubu
                (track_map["Hokubu"], g_car_map["BMW M4"], 57.0, 1140, 2592, 0, None, None, None),
                # Track: Soni
                (track_map["Soni"], g_car_map["BMW M4"], 47.0, 870, 1978, 0, None, None, None),
                # Track: Sekibe
                (track_map["Sekibe"], g_car_map["BMW M4"], 77.0, 961, 2185, 0, None, None, None),
                # Track: Horizon Time Attack Template
                (track_map["Horizon Time Attack Template"], g_car_map["Template Car"], 60.0, 0, 0, 0, None, None, None),
                # Track: Horizon Drift Loop
                (track_map["Horizon Drift Loop"], g_car_map["BMW M4 Drift"], 60.0, 0, 0, 0, 0.7, 0.1, "A_BTN")
            ]
            cursor.executemany("""
            INSERT INTO cars (track_id, global_car_id, time_seconds, xp, cr, skillpoints, drift_interval, drift_duration, drift_button)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, cars_data)
            
    # Ensure cr_multiplier column exists (migration)
    try:
        cursor.execute("SELECT cr_multiplier FROM cars LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE cars ADD COLUMN cr_multiplier REAL DEFAULT 0.0")
        conn.commit()

    # Ensure all default settings are present
    default_settings = [
        ("focus_window_enabled", "True"),
        ("startup_delay", "5"),
        ("autodrive_activation_enabled", "True"),
        ("autodrive_activation_delay", "5.0"),
        ("race_time_buffer", "15"),
        ("video_runs_to_keep", "2"),
        ("control_ACCELERATE", "RT"),
        ("control_BRAKE", "LT"),
        ("control_EBRAKE", "A_BTN"),
        ("control_ACTIVATE", "A_BTN"),
        ("control_START_EVENT", "X_BTN"),
        ("control_ANNA", "DPAD_DOWN"),
        ("control_AUTODRIVE", "DPAD_LEFT")
    ]
    cursor.executemany("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", default_settings)
    conn.commit()
    conn.close()

# Tracks functions
def get_all_tracks():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tracks ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_track(name, track_type, image_path=""):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO tracks (name, type, image_path) VALUES (?, ?, ?)", (name, track_type, image_path))
        conn.commit()
        track_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        track_id = None
    conn.close()
    return track_id

def update_track(track_id, name, track_type, image_path):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tracks SET name=?, type=?, image_path=? WHERE id=?", (name, track_type, image_path, track_id))
    conn.commit()
    conn.close()

def delete_track(track_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tracks WHERE id=?", (track_id,))
    cursor.execute("DELETE FROM cars WHERE track_id=?", (track_id,))
    conn.commit()
    conn.close()

# Cars functions
def get_cars_by_track(track_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cars.id, cars.track_id, cars.global_car_id, cars.time_seconds, cars.xp, cars.cr, cars.cr_multiplier, cars.skillpoints, 
               cars.drift_interval, cars.drift_duration, cars.drift_button,
               global_cars.name, global_cars.image_path
        FROM cars
        JOIN global_cars ON cars.global_car_id = global_cars.id
        WHERE cars.track_id=?
        ORDER BY global_cars.name
    """, (track_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_car_to_track(track_id, global_car_id, time_seconds=60.0, xp=0, cr=0, skillpoints=0):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO cars (track_id, global_car_id, time_seconds, xp, cr, skillpoints)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (track_id, global_car_id, time_seconds, xp, cr, skillpoints))
        conn.commit()
        setup_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        setup_id = None
    conn.close()
    return setup_id

def update_car(car_setup_id, time_seconds, xp, cr, cr_multiplier, skillpoints, drift_interval=None, drift_duration=None, drift_button=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE cars SET time_seconds=?, xp=?, cr=?, cr_multiplier=?, skillpoints=?, drift_interval=?, drift_duration=?, drift_button=?
    WHERE id=?
    """, (time_seconds, xp, cr, cr_multiplier, skillpoints, drift_interval, drift_duration, drift_button, car_setup_id))
    conn.commit()
    conn.close()

def delete_car(car_setup_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cars WHERE id=?", (car_setup_id,))
    conn.commit()
    conn.close()

# Global Cars functions
def get_all_global_cars():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM global_cars ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_global_car(name, image_path=""):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO global_cars (name, image_path) VALUES (?, ?)", (name, image_path))
        conn.commit()
        car_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        car_id = None
    conn.close()
    return car_id

def update_global_car(car_id, name, image_path):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE global_cars SET name=?, image_path=? WHERE id=?", (name, image_path, car_id))
    conn.commit()
    conn.close()

def update_global_car_image_by_setup(car_setup_id, image_path):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT global_car_id FROM cars WHERE id=?", (car_setup_id,))
    row = cursor.fetchone()
    if row:
        g_car_id = row[0]
        cursor.execute("UPDATE global_cars SET image_path=? WHERE id=?", (image_path, g_car_id))
        conn.commit()
    conn.close()

def delete_global_car(car_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM global_cars WHERE id=?", (car_id,))
    cursor.execute("DELETE FROM cars WHERE global_car_id=?", (car_id,))
    conn.commit()
    conn.close()

# Sequence functions
def get_sequence_steps(sequence_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sequences WHERE sequence_name=? ORDER BY step_index ASC", (sequence_name,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_sequence_steps(sequence_name, steps):
    """
    steps: list of dicts with keys: label, action_type, action_value, delay, repetitions
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sequences WHERE sequence_name=?", (sequence_name,))
    
    for idx, step in enumerate(steps, start=1):
        cursor.execute("""
        INSERT INTO sequences (sequence_name, step_index, label, action_type, action_value, delay, repetitions)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (sequence_name, idx, step["label"], step["action_type"], step["action_value"], step["delay"], step["repetitions"]))
        
    conn.commit()
    conn.close()

# Settings functions
def get_settings():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}

def save_setting(key, value):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def get_all_cars():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cars.id, cars.track_id, cars.global_car_id, cars.time_seconds, cars.xp, cars.cr, cars.cr_multiplier, cars.skillpoints, 
               tracks.name AS track_name, tracks.type AS track_type, tracks.image_path AS track_image_path,
               global_cars.name, global_cars.image_path
        FROM cars
        JOIN tracks ON cars.track_id = tracks.id
        JOIN global_cars ON cars.global_car_id = global_cars.id
        ORDER BY global_cars.name
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# History functions
def add_history_record(track_id, car_setup_id, cr, xp, skillpoints):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO history (track_id, car_setup_id, cr, xp, skillpoints)
        VALUES (?, ?, ?, ?, ?)
    """, (track_id, car_setup_id, cr, xp, skillpoints))
    conn.commit()
    conn.close()

def get_history():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT h.id, datetime(h.timestamp, 'localtime') AS timestamp, h.cr, h.xp, h.skillpoints, 
               t.name AS track_name, gc.name AS car_name
        FROM history h
        JOIN tracks t ON h.track_id = t.id
        JOIN cars c ON h.car_setup_id = c.id
        JOIN global_cars gc ON c.global_car_id = gc.id
        ORDER BY h.timestamp DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Run initialization immediately on import to ensure DB exists
init_db()


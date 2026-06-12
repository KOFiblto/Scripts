import sqlite3
import os
from datetime import datetime

DATABASE_PATH = os.environ.get("DATABASE_PATH", "untis_analytics.db")

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Profiles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            server TEXT NOT NULL,
            school TEXT NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            active INTEGER DEFAULT 0,
            last_sync TEXT,
            is_mock INTEGER DEFAULT 0
        );
    """)
    
    # Timetable table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            period_id INTEGER,
            date TEXT NOT NULL,
            start_time TEXT NOT NULL, -- ISO timestamp YYYY-MM-DDTHH:MM:SS
            end_time TEXT NOT NULL,   -- ISO timestamp YYYY-MM-DDTHH:MM:SS
            subject_name TEXT,
            subject_long_name TEXT,
            teacher_name TEXT,
            room_name TEXT,
            FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
        );
    """)
    
    # Absences table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS absences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            absence_id INTEGER,
            profile_id INTEGER NOT NULL,
            date TEXT NOT NULL,       -- YYYY-MM-DD
            start_time TEXT NOT NULL, -- ISO timestamp YYYY-MM-DDTHH:MM:SS
            end_time TEXT NOT NULL,   -- ISO timestamp YYYY-MM-DDTHH:MM:SS
            duration INTEGER NOT NULL, -- in minutes
            status TEXT NOT NULL,      -- excused, unexcused, open
            reason TEXT,
            subject_name TEXT,
            teacher_names TEXT,
            checked INTEGER DEFAULT 0,
            FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
        );
    """)
    
    # Create indexes for faster queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timetable_profile ON timetable(profile_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_absences_profile ON absences(profile_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_absences_date ON absences(date);")
    
    conn.commit()
    conn.close()

# Profile Management functions
def get_profiles():
    conn = get_db_connection()
    profiles = conn.execute("SELECT * FROM profiles ORDER BY name ASC").fetchall()
    conn.close()
    return [dict(p) for p in profiles]

def get_profile(profile_id):
    conn = get_db_connection()
    profile = conn.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
    conn.close()
    return dict(profile) if profile else None

def get_active_profile():
    conn = get_db_connection()
    profile = conn.execute("SELECT * FROM profiles WHERE active = 1").fetchone()
    if not profile:
        # Fallback to first profile if none is active
        profile = conn.execute("SELECT * FROM profiles LIMIT 1").fetchone()
        if profile:
            conn.execute("UPDATE profiles SET active = 1 WHERE id = ?", (profile['id'],))
            conn.commit()
    conn.close()
    return dict(profile) if profile else None

def add_profile(name, server, school, username, password, is_mock=0):
    conn = get_db_connection()
    try:
        # Check if first profile, make active
        cursor = conn.cursor()
        count = cursor.execute("SELECT COUNT(*) FROM profiles").fetchone()[0]
        active = 1 if count == 0 else 0
        
        cursor.execute("""
            INSERT INTO profiles (name, server, school, username, password, active, is_mock)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, server, school, username, password, active, is_mock))
        conn.commit()
        profile_id = cursor.lastrowid
        return profile_id, None
    except sqlite3.IntegrityError:
        return None, "Profile name already exists."
    finally:
        conn.close()

def update_profile(profile_id, name, server, school, username, password):
    conn = get_db_connection()
    try:
        conn.execute("""
            UPDATE profiles 
            SET name = ?, server = ?, school = ?, username = ?, password = ?
            WHERE id = ?
        """, (name, server, school, username, password, profile_id))
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, "Profile name already exists."
    finally:
        conn.close()

def delete_profile(profile_id):
    conn = get_db_connection()
    # Check if we are deleting the active profile
    profile = conn.execute("SELECT active FROM profiles WHERE id = ?", (profile_id,)).fetchone()
    is_active = profile['active'] if profile else 0
    
    conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
    conn.commit()
    
    if is_active:
        # Set another profile active
        new_active = conn.execute("SELECT id FROM profiles LIMIT 1").fetchone()
        if new_active:
            conn.execute("UPDATE profiles SET active = 1 WHERE id = ?", (new_active['id'],))
            conn.commit()
            
    conn.close()
    return True

def set_active_profile(profile_id):
    conn = get_db_connection()
    conn.execute("UPDATE profiles SET active = 0")
    conn.execute("UPDATE profiles SET active = 1 WHERE id = ?", (profile_id,))
    conn.commit()
    conn.close()
    return True

# Data persistence functions
def save_timetable(profile_id, lessons_data):
    """
    lessons_data: list of dicts representing lessons
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Delete old timetable data for this profile
    cursor.execute("DELETE FROM timetable WHERE profile_id = ?", (profile_id,))
    
    # Insert new timetable
    cursor.executemany("""
        INSERT INTO timetable (profile_id, period_id, date, start_time, end_time, subject_name, subject_long_name, teacher_name, room_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [(
        profile_id,
        l.get('period_id'),
        l['date'],
        l['start_time'],
        l['end_time'],
        l.get('subject_name'),
        l.get('subject_long_name'),
        l.get('teacher_name'),
        l.get('room_name')
    ) for l in lessons_data])
    
    conn.commit()
    conn.close()

def save_absences(profile_id, absences_data):
    """
    absences_data: list of dicts representing absences
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Delete old absences data for this profile
    cursor.execute("DELETE FROM absences WHERE profile_id = ?", (profile_id,))
    
    # Insert new absences
    cursor.executemany("""
        INSERT INTO absences (absence_id, profile_id, date, start_time, end_time, duration, status, reason, subject_name, teacher_names, checked)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [(
        a.get('absence_id'),
        profile_id,
        a['date'],
        a['start_time'],
        a['end_time'],
        a['duration'],
        a['status'],
        a.get('reason'),
        a.get('subject_name'),
        a.get('teacher_names'),
        a.get('checked', 0)
    ) for a in absences_data])
    
    # Update last sync timestamp
    now_str = datetime.now().isoformat()
    cursor.execute("UPDATE profiles SET last_sync = ?, is_mock = 0 WHERE id = ?", (now_str, profile_id))
    
    conn.commit()
    conn.close()

def mark_profile_as_mock(profile_id):
    conn = get_db_connection()
    now_str = datetime.now().isoformat()
    conn.execute("UPDATE profiles SET last_sync = ?, is_mock = 1 WHERE id = ?", (now_str, profile_id))
    conn.commit()
    conn.close()

def get_absences(profile_id):
    conn = get_db_connection()
    absences = conn.execute("SELECT * FROM absences WHERE profile_id = ? ORDER BY start_time DESC", (profile_id,)).fetchall()
    conn.close()
    return [dict(a) for a in absences]

def get_timetable(profile_id):
    conn = get_db_connection()
    lessons = conn.execute("SELECT * FROM timetable WHERE profile_id = ? ORDER BY start_time ASC", (profile_id,)).fetchall()
    conn.close()
    return [dict(l) for l in lessons]

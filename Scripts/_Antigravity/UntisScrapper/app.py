import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up database path and secret key
DATABASE_PATH = os.environ.get("DATABASE_PATH", "untis_analytics.db")
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev_secret_key_12345")

# Ensure app is initialized
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Ensure database environment is configured
os.environ["DATABASE_PATH"] = DATABASE_PATH

import database
import webuntis_sync
import mock_data
from datetime import datetime, timedelta

# Initialize database tables on start
database.init_db()

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    active_profile = database.get_active_profile()
    profiles = database.get_profiles()
    
    return render_template(
        'dashboard.html',
        active_profile=active_profile,
        profiles=profiles
    )

@app.route('/profiles', methods=['GET', 'POST'])
def profiles():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            name = request.form.get('name')
            server = request.form.get('server')
            school = request.form.get('school')
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not name or not server or not school or not username or not password:
                flash("All fields are required.", "error")
            else:
                profile_id, err = database.add_profile(name, server, school, username, password)
                if err:
                    flash(err, "error")
                else:
                    flash(f"Profile '{name}' added successfully!", "success")
                    # If this is the active/only profile, redirect to sync
                    return redirect(url_for('sync_page'))
                    
        elif action == 'select':
            profile_id = request.form.get('profile_id')
            if profile_id:
                database.set_active_profile(int(profile_id))
                flash("Active profile updated.", "success")
                
        elif action == 'delete':
            profile_id = request.form.get('profile_id')
            if profile_id:
                database.delete_profile(int(profile_id))
                flash("Profile deleted.", "success")
                
        elif action == 'edit':
            profile_id = request.form.get('profile_id')
            name = request.form.get('name')
            server = request.form.get('server')
            school = request.form.get('school')
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not name or not server or not school or not username or not password:
                flash("All fields are required for editing.", "error")
            else:
                success, err = database.update_profile(int(profile_id), name, server, school, username, password)
                if err:
                    flash(err, "error")
                else:
                    flash("Profile updated successfully.", "success")
                    
        return redirect(url_for('profiles'))
        
    profiles = database.get_profiles()
    active_profile = database.get_active_profile()
    return render_template('profiles.html', profiles=profiles, active_profile=active_profile)

@app.route('/sync', methods=['GET', 'POST'])
def sync_page():
    active_profile = database.get_active_profile()
    profiles = database.get_profiles()
    
    if request.method == 'POST':
        if not active_profile:
            flash("Please create or select a profile first.", "error")
            return redirect(url_for('profiles'))
            
        action = request.form.get('action')
        
        if action == 'sync':
            # Run real sync
            flash("Syncing with WebUntis... Please wait.", "info")
            num_absences, err = webuntis_sync.sync_profile_data(active_profile)
            if err:
                flash(err, "error")
            else:
                flash(f"Sync complete! Retrieved {num_absences} absences and updated local database.", "success")
                return redirect(url_for('dashboard'))
                
        elif action == 'mock':
            # Generate mock data
            mock_data.generate_mock_data(active_profile['id'])
            flash("Mock data generated! Local database populated with synthetic timetable and absences.", "success")
            return redirect(url_for('dashboard'))
            
        return redirect(url_for('sync_page'))
        
    return render_template('sync.html', active_profile=active_profile, profiles=profiles)

PERIOD_START_TIMES = [
    (7, 45),   # P1
    (8, 35),   # P2
    (9, 40),   # P3
    (10, 30),  # P4
    (11, 30),  # P5
    (12, 20),  # P6
    (13, 15),  # P7
    (14, 5),   # P8
    (15, 15),  # P9
    (16, 5),   # P10
]

def get_period_index(dt):
    h, m = dt.hour, dt.minute
    best_idx = None
    min_diff = 9999
    for idx, (ph, pm) in enumerate(PERIOD_START_TIMES):
        diff = abs((h * 60 + m) - (ph * 60 + pm))
        if diff < min_diff:
            min_diff = diff
            best_idx = idx
    if min_diff < 30:
        return best_idx
    return None

def get_period_duration(profile_id):
    return 50.0


@app.route('/api/dashboard_data')
def api_dashboard_data():
    active_profile = database.get_active_profile()
    if not active_profile:
        return jsonify({"success": False, "has_data": False, "error": "No active profile."})
        
    absences = database.get_absences(active_profile['id'])
    
    if not absences:
        return jsonify({
            "success": True, 
            "has_data": False,
            "active_profile_name": active_profile['name'],
            "last_sync": active_profile['last_sync'],
            "is_mock": bool(active_profile['is_mock'])
        })
        
    # Get period duration dynamically
    period_duration = get_period_duration(active_profile['id'])
    
    # Fetch timetable lessons for density mapping
    lessons = database.get_timetable(active_profile['id'])
        
    # Calculate stats
    total_minutes = sum(a['duration'] for a in absences)
    total_hours = round(total_minutes / period_duration, 1)
    
    excused_minutes = sum(a['duration'] for a in absences if a['status'] == 'excused')
    excused_hours = round(excused_minutes / period_duration, 1)
    
    unexcused_minutes = sum(a['duration'] for a in absences if a['status'] == 'unexcused')
    unexcused_hours = round(unexcused_minutes / period_duration, 1)
    
    open_minutes = sum(a['duration'] for a in absences if a['status'] == 'open')
    open_hours = round(open_minutes / period_duration, 1)
    
    # Late arrivals vs full hours missed
    # Late arrival is defined as duration < period_duration
    late_arrivals_count = sum(1 for a in absences if a['duration'] < period_duration)
    full_hours_count = sum(1 for a in absences if a['duration'] >= period_duration)
    
    # Subject breakdown (splitting multi-subject absences equally)
    subject_map = {}
    for a in absences:
        subj_str = a['subject_name'] or "Unknown"
        subjects = [s.strip() for s in subj_str.split(",") if s.strip()]
        if not subjects:
            subjects = ["Unknown"]
        share = a['duration'] / len(subjects)
        for subj in subjects:
            subject_map[subj] = subject_map.get(subj, 0) + share
         
    subjects_list = []
    for subj, mins in subject_map.items():
        subjects_list.append({
            "subject": subj,
            "minutes": int(mins),
            "periods": round(mins / 50.0, 1),
            "clock_hours": round(mins / 60.0, 1),
            "hours": round(mins / period_duration, 1)
        })
    # Sort subjects by hours descending
    subjects_list.sort(key=lambda x: x['hours'], reverse=True)
    
    # Weekday breakdown
    weekday_map = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0} # Mon to Fri
    weekday_names = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday"}
    
    for a in absences:
        try:
            dt = datetime.strptime(a['date'], "%Y-%m-%d")
            wd = dt.weekday()
            if wd < 5: # Only count Monday-Friday
                weekday_map[wd] += a['duration']
        except Exception:
            pass
            
    weekdays_list = []
    for wd in range(5):
        weekdays_list.append({
            "day": weekday_names[wd],
            "hours": round(weekday_map[wd] / period_duration, 1)
        })
        
    # Heatmap data (date_str -> hours)
    heatmap_data = {}
    for a in absences:
        date_str = a['date']
        heatmap_data[date_str] = round(heatmap_data.get(date_str, 0) + (a['duration'] / period_duration), 1)
        
    # Calculate density matrix (5 weekdays x 10 periods)
    density_matrix = [[0.0 for _ in range(10)] for _ in range(5)]
    lessons_by_date = {}
    for l in lessons:
        l_date = l['date']
        if l_date not in lessons_by_date:
            lessons_by_date[l_date] = []
        lessons_by_date[l_date].append(l)
        
    for a in absences:
        try:
            abs_start = datetime.fromisoformat(a['start_time'])
            abs_end = datetime.fromisoformat(a['end_time'])
        except Exception:
            continue
            
        wd = abs_start.weekday()
        if wd >= 5:
            continue
            
        date_str = a['date']
        day_lessons = lessons_by_date.get(date_str, [])
        
        if day_lessons:
            for l in day_lessons:
                try:
                    l_start = datetime.fromisoformat(l['start_time'])
                    l_end = datetime.fromisoformat(l['end_time'])
                except Exception:
                    continue
                overlap_start = max(l_start, abs_start)
                overlap_end = min(l_end, abs_end)
                if overlap_start < overlap_end:
                    p_idx = get_period_index(l_start)
                    if p_idx is not None:
                        overlap_mins = (overlap_end - overlap_start).total_seconds() / 60
                        density_matrix[wd][p_idx] += overlap_mins / 50.0
        else:
            for p_idx, (ph, pm) in enumerate(PERIOD_START_TIMES):
                p_start = datetime.combine(abs_start.date(), datetime.min.time()).replace(hour=ph, minute=pm)
                p_end = p_start + timedelta(minutes=50)
                overlap_start = max(p_start, abs_start)
                overlap_end = min(p_end, abs_end)
                if overlap_start < overlap_end:
                    overlap_mins = (overlap_end - overlap_start).total_seconds() / 60
                    density_matrix[wd][p_idx] += overlap_mins / 50.0
                    
    for r in range(5):
        for c in range(10):
            density_matrix[r][c] = round(density_matrix[r][c], 2)
        
    # Format absences for list view
    formatted_absences = []
    for a in absences:
        # Format start and end
        try:
            start_dt = datetime.fromisoformat(a['start_time'])
            end_dt = datetime.fromisoformat(a['end_time'])
            time_range = f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
        except Exception:
            time_range = ""
            
        formatted_absences.append({
            "id": a['id'],
            "absence_id": a['absence_id'],
            "date": a['date'],
            "time_range": time_range,
            "duration_periods": round(a['duration'] / period_duration, 1),
            "duration_minutes": a['duration'],
            "status": a['status'],
            "reason": a['reason'] or "-",
            "subject": a['subject_name'] or "Unknown",
            "teachers": a['teacher_names'] or "-"
        })
        
    return jsonify({
        "success": True,
        "has_data": True,
        "active_profile_name": active_profile['name'],
        "last_sync": active_profile['last_sync'],
        "is_mock": bool(active_profile['is_mock']),
        "stats": {
            "total_hours": total_hours,
            "excused_hours": excused_hours,
            "unexcused_hours": unexcused_hours,
            "open_hours": open_hours,
            "late_arrivals": late_arrivals_count,
            "full_hours_missed": full_hours_count
        },
        "subjects": subjects_list,
        "weekdays": weekdays_list,
        "heatmap": heatmap_data,
        "density_matrix": density_matrix,
        "absences": formatted_absences
    })

if __name__ == '__main__':
    # Run server locally
    app.run(host='127.0.0.1', port=5000, debug=True)

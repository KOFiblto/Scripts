import random
from datetime import datetime, timedelta
from database import save_timetable, save_absences, mark_profile_as_mock

SUBJECTS = [
    ("MA", "Mathematics"),
    ("DE", "German"),
    ("EN", "English"),
    ("PH", "Physics"),
    ("CH", "Chemistry"),
    ("BI", "Biology"),
    ("GE", "History"),
    ("GG", "Geography"),
    ("SP", "Physical Education"),
    ("KU", "Art")
]

TEACHERS = ["Mr. Smith", "Mrs. Davis", "Dr. Meyer", "Mr. Jones", "Mrs. Wilson", "Mrs. Brown"]
ROOMS = ["101", "102", "Lab A", "Gym", "Art Room", "204"]

def generate_mock_data(profile_id):
    # Set date range: last 9 months up to today
    today = datetime.now().date()
    start_date = today - timedelta(days=270)
    
    # 1. Generate Timetable Lessons
    lessons = []
    current_date = start_date
    period_id = 1
    
    # Typical school times (6 periods per day, 50 mins each)
    period_times = [
        ("08:00:00", "08:50:00"),
        ("08:55:00", "09:45:00"),
        ("10:00:00", "10:50:00"),
        ("10:55:00", "11:45:00"),
        ("12:00:00", "12:50:00"),
        ("12:55:00", "13:45:00")
    ]
    
    # We populate lessons for every weekday (Monday to Friday)
    while current_date <= today:
        if current_date.weekday() < 5:  # Mon-Fri
            for period_idx, (start_t, end_t) in enumerate(period_times):
                # Pick a subject based on weekday and period to keep it semi-consistent
                seed = (current_date.weekday() * 7 + period_idx) % len(SUBJECTS)
                subj_name, subj_long = SUBJECTS[seed]
                teacher = TEACHERS[seed % len(TEACHERS)]
                room = ROOMS[seed % len(ROOMS)]
                
                lessons.append({
                    "period_id": period_id,
                    "date": current_date.isoformat(),
                    "start_time": f"{current_date.isoformat()}T{start_t}",
                    "end_time": f"{current_date.isoformat()}T{end_t}",
                    "subject_name": subj_name,
                    "subject_long_name": subj_long,
                    "teacher_name": teacher,
                    "room_name": room
                })
                period_id += 1
        current_date += timedelta(days=1)
        
    save_timetable(profile_id, lessons)
    
    # 2. Generate Absences
    absences = []
    current_date = start_date
    absence_id = 100
    
    # Generate some absences
    while current_date <= today:
        if current_date.weekday() < 5:
            # Random chance of absence on this day
            rand = random.random()
            
            # 3% chance of a full day absence (e.g. sick)
            if rand < 0.03:
                # Full day absence (all 6 periods)
                start_t = "08:00:00"
                end_t = "13:15:00"
                duration = 315 # minutes
                status = random.choices(["excused", "unexcused", "open"], weights=[0.8, 0.1, 0.1])[0]
                reason = random.choice(["Sick", "Doctor's Appointment", "Family reasons", ""]) if status == "excused" else ""
                
                absences.append({
                    "absence_id": absence_id,
                    "date": current_date.isoformat(),
                    "start_time": f"{current_date.isoformat()}T{start_t}",
                    "end_time": f"{current_date.isoformat()}T{end_t}",
                    "duration": duration,
                    "status": status,
                    "reason": reason,
                    "subject_name": "Multiple",
                    "teacher_names": "Multiple",
                    "checked": 1 if status != "open" else 0
                })
                absence_id += 1
                
            # 5% chance of a single period absence
            elif rand < 0.08:
                period_idx = random.randint(0, 5)
                start_t, end_t = period_times[period_idx]
                duration = 50
                status = random.choices(["excused", "unexcused", "open"], weights=[0.7, 0.15, 0.15])[0]
                reason = random.choice(["Train delayed", "Overslept", "Dentist", ""]) if status == "excused" else ""
                
                # Find matching subject
                seed = (current_date.weekday() * 7 + period_idx) % len(SUBJECTS)
                subj_name, _ = SUBJECTS[seed]
                teacher = TEACHERS[seed % len(TEACHERS)]
                
                absences.append({
                    "absence_id": absence_id,
                    "date": current_date.isoformat(),
                    "start_time": f"{current_date.isoformat()}T{start_t}",
                    "end_time": f"{current_date.isoformat()}T{end_t}",
                    "duration": duration,
                    "status": status,
                    "reason": reason,
                    "subject_name": subj_name,
                    "teacher_names": teacher,
                    "checked": 1 if status != "open" else 0
                })
                absence_id += 1
                
            # 4% chance of a late arrival (Zuspätkommen)
            elif rand < 0.12:
                # Late arrival in the first period
                start_t = "08:00:00"
                # Arrived late by 10 to 30 minutes
                late_mins = random.randint(10, 30)
                end_datetime = datetime.combine(current_date, datetime.strptime("08:00:00", "%H:%M:%S").time()) + timedelta(minutes=late_mins)
                end_t = end_datetime.strftime("%H:%M:%S")
                
                duration = late_mins
                status = random.choices(["excused", "unexcused", "open"], weights=[0.6, 0.2, 0.2])[0]
                reason = random.choice(["Bus missed", "Traffic jam", "Alarm clock failed", ""]) if status == "excused" else ""
                
                seed = (current_date.weekday() * 7) % len(SUBJECTS)
                subj_name, _ = SUBJECTS[seed]
                teacher = TEACHERS[seed % len(TEACHERS)]
                
                absences.append({
                    "absence_id": absence_id,
                    "date": current_date.isoformat(),
                    "start_time": f"{current_date.isoformat()}T{start_t}",
                    "end_time": f"{current_date.isoformat()}T{end_t}",
                    "duration": duration,
                    "status": status,
                    "reason": reason,
                    "subject_name": subj_name,
                    "teacher_names": teacher,
                    "checked": 1 if status != "open" else 0
                })
                absence_id += 1
                
        current_date += timedelta(days=1)
        
    save_absences(profile_id, absences)
    mark_profile_as_mock(profile_id)
    print(f"Generated mock data for profile {profile_id}: {len(lessons)} lessons, {len(absences)} absences.")

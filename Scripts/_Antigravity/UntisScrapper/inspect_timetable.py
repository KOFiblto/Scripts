import database
import webuntis
from datetime import datetime, timedelta
import json

profile = database.get_active_profile()
if not profile:
    print("No active profile.")
    exit(1)

server = profile['server'].replace("https://", "").replace("http://", "").split("/")[0]

session = webuntis.Session(
    server=server,
    school=profile['school'],
    username=profile['username'],
    password=profile['password'],
    useragent="WebUntisAnalyticsDashboard/1.0"
)

try:
    session.login()
    print("Login successful.")
    
    # Get last 30 days
    today = datetime.now()
    start_date = today - timedelta(days=30)
    end_date = today
    
    print(f"Fetching timetable from {start_date.date()} to {end_date.date()}...")
    
    lessons = session.my_timetable(start=start_date, end=end_date)
    print(f"Retrieved {len(lessons)} periods.")
    
    # Print distinct keys in raw data and inspect some lessons
    all_keys = set()
    for l in lessons:
        all_keys.update(l._data.keys())
        
    print("\nAll keys found in raw period data:")
    print(list(all_keys))
    
    # Find lessons with code or text or other interesting attributes
    interesting_lessons = []
    for l in lessons:
        data = l._data
        # check if it has cancelled code, irregular code, bkRemark, bkText, lstext, info, etc.
        has_interest = (
            data.get('code') is not None or 
            data.get('lstext') != '' or 
            data.get('info') != '' or 
            data.get('statflags') != '' or
            data.get('bkRemark') != '' or
            data.get('bkText') != '' or
            data.get('substText') != ''
        )
        if has_interest:
            interesting_lessons.append(l)
            
    print(f"\nFound {len(interesting_lessons)} lessons with special attributes.")
    for l in interesting_lessons[:10]:
        print("\n--- Lesson Details ---")
        print(f"Date: {l.start.date()}, Time: {l.start.time()} - {l.end.time()}")
        print(f"Subject: {l.subjects[0].name if l.subjects else 'None'}")
        print("Raw Data:", json.dumps(l._data, indent=2))
        
    session.logout()
except Exception as e:
    print("Error:", str(e))

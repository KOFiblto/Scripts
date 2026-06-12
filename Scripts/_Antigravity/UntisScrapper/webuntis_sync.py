import webuntis
import webuntis.utils.remote
import webuntis.errors
from datetime import datetime, timedelta
from database import save_timetable, save_absences
import pyotp
import requests
import json
import time
import re

def calculate_true_absence_duration(start_dt, end_dt, lessons_data):
    """
    Finds all active lessons that overlap with [start_dt, end_dt],
    merges overlapping segments, and returns the total duration in minutes.
    If no overlapping lessons are scheduled, falls back to the raw duration.
    """
    start_dt = start_dt.replace(tzinfo=None)
    end_dt = end_dt.replace(tzinfo=None)
    
    intervals = []
    for l in lessons_data:
        try:
            l_start = datetime.fromisoformat(l['start_time']).replace(tzinfo=None)
            l_end = datetime.fromisoformat(l['end_time']).replace(tzinfo=None)
        except Exception:
            continue
        
        # Intersect [l_start, l_end] with [start_dt, end_dt]
        overlap_start = max(l_start, start_dt)
        overlap_end = min(l_end, end_dt)
        if overlap_start < overlap_end:
            intervals.append((overlap_start, overlap_end))
            
    if not intervals:
        raw_dur = int((end_dt - start_dt).total_seconds() / 60)
        return max(raw_dur, 45)
        
    # Merge intervals
    intervals.sort(key=lambda x: x[0])
    merged = []
    for start, end in intervals:
        if not merged or merged[-1][1] < start:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
            
    total_mins = sum((end - start).total_seconds() / 60 for start, end in merged)
    return int(total_mins)

def is_totp_secret(secret):
    if not secret:
        return False
    clean = secret.strip().upper()
    return len(clean) == 16 and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567' for c in clean)



# Monkeypatch python-webuntis to prevent "Request ID was not the same one as returned"
# when the server returns 'error' as ID on failures.
def custom_parse_result(request_body, result_body):
    if request_body.get('id') != result_body.get('id'):
        # If the server returned 'error' as the ID and there is an error field,
        # it is a JSON-RPC level error (e.g. bad credentials). Allow it to parse the error.
        if result_body.get('id') == 'error' and 'error' in result_body:
            pass
        else:
            raise webuntis.errors.RemoteError(
                'Request ID was not the same one as returned. %s -- %s' % (request_body.get('id'), result_body.get('id'))
            )
    try:
        return result_body['result']
    except KeyError:
        webuntis.utils.remote._parse_error_code(request_body, result_body)

webuntis.utils.remote._parse_result = custom_parse_result

def clean_server_url(url):
    # Remove http:// or https:// and any trailing slash or path if entered by the user
    clean = url.strip()
    if clean.startswith("https://"):
        clean = clean[8:]
    elif clean.startswith("http://"):
        clean = clean[7:]
    if "/" in clean:
        clean = clean.split("/")[0]
    return clean

def sync_profile_data(profile):
    """
    Logins to WebUntis with profile credentials,
    fetches timetable and absence data,
    resolves subject names for absences,
    and caches them in SQLite.
    
    Returns (num_absences_synced, error_message)
    """
    server = clean_server_url(profile['server'])
    school = profile['school'].strip()
    username = profile['username'].strip()
    password = profile['password']
    
    is_totp = is_totp_secret(password)
    
    session_id = None
    person_id = None
    person_type = 5  # default to student (5)
    
    if is_totp:
        totp = pyotp.TOTP(password.strip().upper())
        otp_code = totp.now()
        
        login_url = f"https://{server}/WebUntis/jsonrpc_intern.do?school={school}"
        headers = {
            'User-Agent': 'WebUntisAnalyticsDashboard/1.0',
            'Content-Type': 'application/json'
        }
        login_payload = {
            "id": "1",
            "jsonrpc": "2.0",
            "method": "getUserData2017",
            "params": [
                {
                    "auth": {
                        "clientTime": int(time.time() * 1000),
                        "user": username,
                        "otp": otp_code
                    }
                }
            ]
        }
        try:
            r = requests.post(login_url, json=login_payload, headers=headers, timeout=15)
            res = r.json()
            if 'result' in res:
                session_id = r.cookies.get('JSESSIONID')
                user_data = res['result'].get('userData', {})
                person_id = user_data.get('elemId')
                person_type_str = user_data.get('elemType')
                if person_type_str == 'STUDENT':
                    person_type = 5
                elif person_type_str == 'TEACHER':
                    person_type = 2
                else:
                    person_type = 5
            else:
                return None, f"OTP Login failed: {res.get('error', {}).get('message', 'Unknown error')}"
        except Exception as e:
            return None, f"OTP Login connection failed: {str(e)}"
    else:
        session = webuntis.Session(
            server=server,
            school=school,
            username=username,
            password=password,
            useragent="WebUntisAnalyticsDashboard/1.0"
        )
        try:
            session.login()
            session_id = session.config['jsessionid']
            person_id = session.login_result.get('personId')
            person_type = session.login_result.get('personType', 5)
        except webuntis.errors.BadCredentialsError:
            return None, "Invalid credentials. Please verify server, school, username, and password."
        except webuntis.errors.AuthError as e:
            return None, f"Authentication failed: {str(e)}"
        except Exception as e:
            return None, f"Connection failed: {str(e)}"

    # Recreate the python-webuntis Session object using the JSESSIONID (works for both standard and TOTP logins)
    session = webuntis.Session(
        server=server,
        school=school,
        username=username,
        password="",
        jsessionid=session_id,
        useragent="WebUntisAnalyticsDashboard/1.0"
    )
    session.login_result = {
        'personId': person_id,
        'personType': person_type
    }
        
    try:
        # Get start and end date for sync
        # We target the current school year
        try:
            curr_year = session.schoolyears().current
            start_date = curr_year.start
            end_date = curr_year.end
        except Exception:
            # Fallback based on calendar date if API call fails
            today = datetime.now().date()
            if today.month >= 8:
                start_date = datetime(today.year, 9, 1)
                end_date = datetime(today.year + 1, 7, 31)
            else:
                start_date = datetime(today.year - 1, 9, 1)
                end_date = datetime(today.year, 7, 31)
                
        # 1. Fetch timetable lessons for mapping
        try:
            lessons_list = session.my_timetable(start=start_date, end=end_date)
        except Exception as e:
            # Try fallback: fetch student timetable using personId from login result
            if person_id:
                if person_type == 5:
                    lessons_list = session.timetable(start=start_date, end=end_date, student=person_id)
                else:
                    lessons_list = session.timetable(start=start_date, end=end_date, teacher=person_id)
            else:
                raise e
                
        lessons_data = []
        for l in lessons_list:
            # Skip cancelled lessons
            if getattr(l, 'code', None) == 'cancelled' or (hasattr(l, '_data') and l._data.get('code') == 'cancelled'):
                continue
                
            subj_name = ""
            subj_long = ""
            try:
                if l.subjects:
                    subj_name = l.subjects[0].name
                    subj_long = l.subjects[0].long_name
            except Exception:
                su_list = l._data.get('su', [])
                if su_list:
                    subj_name = su_list[0].get('name', '')
                    subj_long = su_list[0].get('longname', '')
                
            teacher_name = ""
            try:
                if l.teachers:
                    teacher_name = l.teachers[0].name
            except Exception:
                te_list = l._data.get('te', [])
                if te_list:
                    teacher_name = te_list[0].get('name', '')
                    if not teacher_name and te_list[0].get('id'):
                        teacher_name = f"ID: {te_list[0].get('id')}"
                
            room_name = ""
            try:
                if l.rooms:
                    room_name = l.rooms[0].name
            except Exception:
                ro_list = l._data.get('ro', [])
                if ro_list:
                    room_name = ro_list[0].get('name', '')
                
            lessons_data.append({
                "period_id": l.id,
                "date": l.start.strftime('%Y-%m-%d'),
                "start_time": l.start.isoformat(),
                "end_time": l.end.isoformat(),
                "subject_name": subj_name,
                "subject_long_name": subj_long,
                "teacher_name": teacher_name,
                "room_name": room_name
            })
            
        save_timetable(profile['id'], lessons_data)
        
        # 2. Fetch student absences
        absences_data = []
        
        if is_totp:
            totp = pyotp.TOTP(password.strip().upper())
            headers = {
                'User-Agent': 'WebUntisAnalyticsDashboard/1.0',
                'Content-Type': 'application/json'
            }
            absences_url = f"https://{server}/WebUntis/jsonrpc_intern.do?school={school}"
            start_dash = start_date.strftime('%Y-%m-%d')
            end_dash = end_date.strftime('%Y-%m-%d')
            
            absences_payload = {
                "id": "2",
                "jsonrpc": "2.0",
                "method": "getStudentAbsences2017",
                "params": [
                    {
                        "auth": {
                            "clientTime": int(time.time() * 1000),
                            "user": username,
                            "otp": totp.now()
                        },
                        "startDate": start_dash,
                        "endDate": end_dash,
                        "includeExcused": True,
                        "includeUnExcused": True
                    }
                ]
            }
            
            r_abs = requests.post(absences_url, json=absences_payload, headers=headers, timeout=15)
            res_abs = r_abs.json()
            if 'result' in res_abs:
                result_data = res_abs['result']
                absences_list_raw = []
                if isinstance(result_data, list):
                    absences_list_raw = result_data
                elif isinstance(result_data, dict):
                    absences_list_raw = result_data.get('absences', [])
                for ab_raw in absences_list_raw:
                    absence_id = ab_raw.get('id')
                    start_dt = datetime.fromisoformat(ab_raw['startDateTime'].replace('Z', ''))
                    end_dt = datetime.fromisoformat(ab_raw['endDateTime'].replace('Z', ''))
                    
                    duration = calculate_true_absence_duration(start_dt, end_dt, lessons_data)
                    
                    date_str = start_dt.strftime('%Y-%m-%d')
                    
                    status_str = "open"
                    excuse_obj = ab_raw.get('excuse') or {}
                    excuse_status_id = excuse_obj.get('excuseStatusId')
                    
                    if ab_raw.get('excused') == True or ab_raw.get('isExcuseStatusExcused') == True or excuse_status_id == 1:
                        status_str = "excused"
                    elif ab_raw.get('isExcuseStatusUnexcused') == True or excuse_status_id == 2:
                        status_str = "unexcused"
                    else:
                        reason_lower = (ab_raw.get('absenceReason') or "").lower()
                        text_lower = (ab_raw.get('text') or "").lower()
                        status_field_lower = str(ab_raw.get('status', '')).lower()
                        
                        if any(x in reason_lower or x in text_lower or x in status_field_lower 
                               for x in ["nicht", "unentschuldigt", "unexcused"]):
                            status_str = "unexcused"
                        elif any(x in reason_lower or x in text_lower or x in status_field_lower 
                                 for x in ["entschuldigt", "excused"]):
                            status_str = "excused"
                        else:
                            status_str = "open"
                            
                    reason_str = ab_raw.get('text') or ab_raw.get('absenceReason') or ""
                    
                    # Resolve subjects and teachers from overlapping active lessons
                    overlapping = []
                    for l in lessons_data:
                        l_start = datetime.fromisoformat(l['start_time'])
                        l_end = datetime.fromisoformat(l['end_time'])
                        if l_start < end_dt and l_end > start_dt:
                            overlapping.append(l)
                            
                    if overlapping:
                        seen_sub = []
                        seen_tea = []
                        for l in overlapping:
                            sub = l.get('subject_name')
                            if sub and sub not in seen_sub:
                                seen_sub.append(sub)
                            tea = l.get('teacher_name')
                            if tea and tea not in seen_tea:
                                seen_tea.append(tea)
                        subj_name = ", ".join(seen_sub) if seen_sub else "Unknown"
                        teacher_names = ", ".join(seen_tea) if seen_tea else ""
                    else:
                        subj_name = "Unknown"
                        teacher_names = ""
                        
                    absences_data.append({
                        "absence_id": absence_id,
                        "date": date_str,
                        "start_time": start_dt.isoformat(),
                        "end_time": end_dt.isoformat(),
                        "duration": duration,
                        "status": status_str,
                        "reason": reason_str,
                        "subject_name": subj_name,
                        "teacher_names": teacher_names,
                        "checked": 0
                    })
            else:
                return None, f"Failed to retrieve student absences: {res_abs.get('error', {}).get('message', 'Unknown error')}"
        else:
            try:
                absences_list = session.timetable_with_absences(start=start_date, end=end_date)
            except webuntis.errors.RemoteError as re:
                if "right" in str(re).lower() or "permission" in str(re).lower() or "authorized" in str(re).lower() or getattr(re, 'code', None) == -8509:
                    return None, (
                        "Permission denied for fetching absences. Standard password logins do not have access to absences. "
                        "Please retrieve your 16-character Mobile Access Key from the WebUntis web portal (under Profile -> Data Access / Mobile Devices) "
                        "and enter it as your Password/Key in the Profile settings to sync absences."
                    )
                raise re
                
            for ab in absences_list:
                date_str = ab.start.strftime('%Y-%m-%d')
                start_iso = ab.start.isoformat()
                end_iso = ab.end.isoformat()
                
                duration = calculate_true_absence_duration(ab.start, ab.end, lessons_data)
                        
                reason_str = ab.reason or ""
                
                status_str = "open"
                if ab.status:
                    status_lower = ab.status.lower()
                    if status_lower.startswith('e') or 'entschuldigt' in status_lower:
                        status_str = "excused"
                    elif status_lower.startswith('u') or 'nicht' in status_lower or status_lower.startswith('n'):
                        status_str = "unexcused"
                
                subj_name = ""
                try:
                    if ab.subject and hasattr(ab.subject, 'name') and ab.subject.name:
                        subj_name = ab.subject.name
                except Exception:
                    pass
                
                teacher_names = ""
                try:
                    if ab.teachers:
                        teacher_names = ", ".join(t.name for t in ab.teachers)
                except Exception:
                    te_ids = ab._data.get('teacherIds', [])
                    if te_ids:
                        teacher_names = ", ".join(f"ID: {tid}" for tid in te_ids if tid)
                    
                if not subj_name:
                    overlapping = []
                    for l in lessons_data:
                        l_start = datetime.fromisoformat(l['start_time'])
                        l_end = datetime.fromisoformat(l['end_time'])
                        if l_start < ab.end and l_end > ab.start:
                            overlapping.append(l)
                    if overlapping:
                        seen_sub = []
                        seen_tea = []
                        for l in overlapping:
                            sub = l.get('subject_name')
                            if sub and sub not in seen_sub:
                                seen_sub.append(sub)
                            tea = l.get('teacher_name')
                            if tea and tea not in seen_tea:
                                seen_tea.append(tea)
                        subj_name = ", ".join(seen_sub) if seen_sub else "Unknown"
                        if not teacher_names:
                            teacher_names = ", ".join(seen_tea) if seen_tea else ""
                    else:
                        subj_name = "Unknown"
                    
                absences_data.append({
                    "absence_id": ab.id,
                    "date": date_str,
                    "start_time": start_iso,
                    "end_time": end_iso,
                    "duration": duration,
                    "status": status_str,
                    "reason": reason_str,
                    "subject_name": subj_name,
                    "teacher_names": teacher_names,
                    "checked": 1 if ab.checked else 0
                })
                
        save_absences(profile['id'], absences_data)
        return len(absences_data), None
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Sync error: {str(e)}"
    finally:
        try:
            session.logout()
        except Exception:
            pass

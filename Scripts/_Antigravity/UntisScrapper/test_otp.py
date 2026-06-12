import pyotp
import requests
import json
from datetime import datetime, timedelta

shared_secret = "ECQG6QRXSZJLCOKG"
totp = pyotp.TOTP(shared_secret)
otp_code = totp.now()

print(f"Generated OTP: {otp_code}")

url = "https://bulme.webuntis.com/WebUntis/jsonrpc.do?school=bulme"

headers = {
    'User-Agent': 'WebUntisAnalyticsDashboard/1.0',
    'Content-Type': 'application/json'
}

payload = {
    "id": str(int(datetime.now().timestamp() * 1000)),
    "jsonrpc": "2.0",
    "method": "authenticate",
    "params": {
        "user": "mathias.kornschober",
        "otp": otp_code,
        "client": "WebUntisAnalyticsDashboard/1.0"
    }
}

r = requests.post(url, json=payload, headers=headers)
res = r.json()
print("Auth Response:")
print(json.dumps(res, indent=2))

if 'result' in res and 'sessionId' in res['result']:
    session_id = res['result']['sessionId']
    print(f"Auth Success! Session ID: {session_id}")
    
    # Try querying timetable with absences!
    today = datetime.now()
    start_date = today - timedelta(days=60)
    end_date = today
    
    start_int = int(start_date.strftime('%Y%m%d'))
    end_int = int(end_date.strftime('%Y%m%d'))
    
    payload_absences = {
        "id": str(int(datetime.now().timestamp() * 1000) + 1),
        "jsonrpc": "2.0",
        "method": "getTimetableWithAbsences",
        "params": {
            "options": {
                "startDate": start_int,
                "endDate": end_int
            }
        }
    }
    
    headers['Cookie'] = f"JSESSIONID={session_id}"
    r_abs = requests.post(url, json=payload_absences, headers=headers)
    print("\nAbsences Response:")
    print(json.dumps(r_abs.json(), indent=2)[:2000])
else:
    print("Auth Failed.")

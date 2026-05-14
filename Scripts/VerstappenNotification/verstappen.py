import os
import time
import argparse
import requests
from bs4 import BeautifulSoup

TIMING_URL = "https://livetiming.azurewebsites.net/event=50?config=w3"
TOPIC = "max_verstappen_24h_v82"
CAR_NUMBER = "3"
DRIVER_NAME = "Verstappen"
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.txt")

def send_notification(message):
    try:
        requests.post(f"https://ntfy.sh/{TOPIC}",
                      data=message.encode(encoding='utf-8'),
                      headers={"Title": "24h Nürburgring", "Priority": "high"})
    except Exception as e:
        print(f"Notification Error: {e}")

def get_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return f.read().strip() == "True"
    return False

def save_state(state):
    with open(STATE_FILE, "w") as f:
        f.write(str(state))

def check_status(is_active):
    try:
        r = requests.get(TIMING_URL, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        for row in soup.find_all('tr'):
            col_no = row.find('td', class_='tc-startingNumber')
            if col_no and col_no.text.strip() == CAR_NUMBER:
                col_driver = row.find('td', class_='tc-driverName')
                if col_driver:
                    is_driving = DRIVER_NAME.lower() in col_driver.text.strip().lower()
                    
                    if is_driving and not is_active:
                        send_notification("MAX IS ON TRACK")
                        return True
                    elif not is_driving and is_active:
                        send_notification("STINT FINISHED")
                        return False
                break
    except Exception as e:
        print(f"Polling Error: {e}")
    return is_active

def monitor(continuous):
    is_active = get_state()
    
    if continuous:
        while True:
            new_state = check_status(is_active)
            if new_state != is_active:
                is_active = new_state
                save_state(is_active)
            time.sleep(30)
    else:
        new_state = check_status(is_active)
        if new_state != is_active:
            save_state(new_state)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--continuous', action='store_true')
    args = parser.parse_args()
    monitor(args.continuous)
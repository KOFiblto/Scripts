# verstappen.py
import time
import requests
from bs4 import BeautifulSoup

TIMING_URL = "https://livetiming.azurewebsites.net/event=50?config=w3"
TOPIC = "max_verstappen_24h_v82"
CAR_NUMBER = "3"
DRIVER_NAME = "Verstappen"

def send_notification(message):
    try:
        requests.post(f"https://ntfy.sh/{TOPIC}",
                      data=message.encode(encoding='utf-8'),
                      headers={"Title": "24h Nürburgring", "Priority": "high"})
    except Exception as e:
        print(f"Notification Error: {e}")

def monitor():
    is_active = False
    print(f"Monitoring Car {CAR_NUMBER}...")
    send_notification("Skript gestartet. Monitoring aktiv.")
    
    while True:
        try:
            r = requests.get(TIMING_URL, timeout=5)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            for row in soup.find_all('tr'):
                col_no = row.find('td', class_='tc-startingNumber')
                if col_no and col_no.text.strip() == CAR_NUMBER:
                    col_driver = row.find('td', class_='tc-driverName')
                    if col_driver:
                        current = col_driver.text.strip().lower()
                        is_driving = DRIVER_NAME.lower() in current
                        
                        if is_driving and not is_active:
                            send_notification("MAX IS ON TRACK")
                            is_active = True
                        elif not is_driving and is_active:
                            send_notification("STINT FINISHED")
                            is_active = False
                    break
        except Exception as e:
            print(f"Polling Error: {e}")
            
        time.sleep(30)

if __name__ == "__main__":
    monitor()
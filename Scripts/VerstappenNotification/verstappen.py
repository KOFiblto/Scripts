import os
import time
from datetime import datetime
import argparse
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

TIMING_URL = "https://livetiming.azurewebsites.net/event=50?config=w3"
TOPIC = "max_verstappen_24h_v82"
CAR_NUMBER = "3"
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log.log")

def send_notification(title, body):
    try:
        safe_title = title.encode('utf-8').decode('latin-1', 'ignore')
        requests.post(f"https://ntfy.sh/{TOPIC}",
                      data=body.encode(encoding='utf-8'),
                      headers={"Title": safe_title, "Priority": "high"})
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Notification Error: {e}")

def get_car_status(driver):
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        car_status = {}
        second_place_gap = None
        
        for row in soup.find_all('tr'):
            col_no = row.find('td', class_='tc-startingNumber')
            col_pos = row.find('td', class_='tc-position')
            col_gap = row.find('td', class_='tc-gap')
            
            if not col_no:
                continue
                
            no_text = col_no.text.strip()
            pos_text = col_pos.text.strip() if col_pos else "N/A"
            gap_text = col_gap.text.strip() if col_gap else "N/A"
            
            if no_text == CAR_NUMBER:
                col_driver = row.find('td', class_='tc-driverName')
                col_lap = row.find('td', class_='tc-laps')
                
                car_status['driver'] = col_driver.text.strip() if col_driver else "Unknown"
                car_status['pos'] = pos_text
                car_status['gap'] = gap_text
                car_status['lap'] = col_lap.text.strip() if col_lap else "N/A"
                
            if pos_text == "2":
                second_place_gap = gap_text
                
        if not car_status:
            return None
            
        if car_status['pos'] == "1":
            car_status['gap'] = second_place_gap if second_place_gap else "N/A"
            
        return car_status
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Polling Error: {e}")
        return None

def write_to_log(status):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"{timestamp},{status['driver']},{status['pos']},{status['lap']},{status['gap']}\n"
    try:
        with open(LOG_FILE, "a", encoding='utf-8') as f:
            f.write(log_line)
    except Exception as e:
        print(f"[{timestamp}] File Log Error: {e}")

def monitor():
    last_driver = None
    last_pos = None
    last_lap = None
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starter Überwachung für Auto {CAR_NUMBER}...")
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--log-level=3')
    
    web_driver = webdriver.Chrome(options=options)
    
    try:
        web_driver.get(TIMING_URL)
        time.sleep(10)
        
        while True:
            status = get_car_status(web_driver)
            
            if status:
                current_driver = status['driver']
                current_pos = status['pos']
                current_lap = status['lap']
                
                write_to_log(status)
                
                driver_changed = (last_driver is not None and current_driver != last_driver)
                pos_changed = (last_pos is not None and current_pos != last_pos)
                lap_changed = (last_lap is not None and current_lap != last_lap)
                
                if driver_changed or pos_changed or lap_changed or last_driver is None:
                    if driver_changed:
                        title = f"{last_driver} -> {current_driver}"
                    else:
                        title = f"{current_driver}"
                        
                    body = f"POS: {status['pos']}\nGAP: {status['gap']}\nLAP: {status['lap']}"
                    
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {title} | POS: {status['pos']} | GAP: {status['gap']} | LAP: {status['lap']}")
                    send_notification(title, body)
                    
                last_driver = current_driver
                last_pos = current_pos
                last_lap = current_lap
                
                time.sleep(10)
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Auto {CAR_NUMBER} nicht gefunden. Lade Seite neu.")
                web_driver.refresh()
                time.sleep(10)
    finally:
        web_driver.quit()

if __name__ == "__main__":
    monitor()
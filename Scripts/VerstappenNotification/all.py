import os
import time
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

TIMING_URL = "https://livetiming.azurewebsites.net/event=50?config=w3"
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "all.log")

def log_change(car_no, status):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"{timestamp},{car_no},{status['pos']},{status['driver']},{status['time']}\n"
    try:
        with open(LOG_FILE, "a", encoding='utf-8') as f:
            f.write(log_line)
    except Exception as e:
        print(f"[{timestamp}] File Log Error: {e}")

def monitor():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starte SP 9 Überwachung...")
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--log-level=3')
    
    web_driver = webdriver.Chrome(options=options)
    previous_states = {}
    
    try:
        web_driver.get(TIMING_URL)
        time.sleep(10)
        
        while True:
            soup = BeautifulSoup(web_driver.page_source, 'html.parser')
            current_cars = {}
            
            for row in soup.find_all('tr'):
                col_no = row.find('td', class_='tc-startingNumber')
                col_class = row.find('td', class_='tc-className')
                
                if col_no and col_class and col_class.text.strip() == "SP 9":
                    car_no = col_no.text.strip()
                    col_pos = row.find('td', class_='tc-position')
                    col_driver = row.find('td', class_='tc-driverName')
                    col_time = row.find('td', class_='tc-lastLapTime')
                    
                    current_cars[car_no] = {
                        'pos': col_pos.text.strip() if col_pos else "N/A",
                        'driver': col_driver.text.strip() if col_driver else "N/A",
                        'time': col_time.text.strip() if col_time else "N/A"
                    }
            
            if not current_cars:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Keine SP 9 Fahrzeuge gefunden. Lade Seite neu.")
                web_driver.refresh()
                time.sleep(10)
                continue

            for car_no, state in current_cars.items():
                if car_no not in previous_states:
                    previous_states[car_no] = state
                    log_change(car_no, state)
                else:
                    prev = previous_states[car_no]
                    if prev['pos'] != state['pos'] or prev['driver'] != state['driver'] or prev['time'] != state['time']:
                        previous_states[car_no] = state
                        log_change(car_no, state)
            
            time.sleep(10)
            
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fatal Error: {e}")
    finally:
        web_driver.quit()

if __name__ == "__main__":
    monitor()
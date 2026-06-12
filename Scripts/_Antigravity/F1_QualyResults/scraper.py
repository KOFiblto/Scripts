import sqlite3
import requests
import time

DB_PATH = 'qualifying.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            driver_id TEXT PRIMARY KEY,
            given_name TEXT,
            family_name TEXT,
            code TEXT,
            permanent_number TEXT,
            nationality TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS races (
            race_id TEXT PRIMARY KEY,
            season INTEGER,
            round INTEGER,
            race_name TEXT,
            date TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            result_id TEXT PRIMARY KEY,
            race_id TEXT,
            driver_id TEXT,
            constructor_id TEXT,
            constructor_name TEXT,
            position INTEGER,
            q1 TEXT,
            q2 TEXT,
            q3 TEXT,
            FOREIGN KEY (race_id) REFERENCES races(race_id),
            FOREIGN KEY (driver_id) REFERENCES drivers(driver_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def fetch_and_store_season(season):
    print(f"Fetching qualifying results for season {season}...")
    limit = 100
    offset = 0
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        while True:
            url = f"https://api.jolpi.ca/ergast/f1/{season}/qualifying.json?limit={limit}&offset={offset}"
            response = requests.get(url, timeout=20)
            if response.status_code != 200:
                print(f"Failed to fetch season {season} at offset {offset}: HTTP {response.status_code}")
                conn.close()
                return False
            
            data = response.json()
            race_list = data.get('MRData', {}).get('RaceTable', {}).get('Races', [])
            
            if not race_list:
                break
                
            for race in race_list:
                race_id = f"{race['season']}_{race['round']}"
                season_num = int(race['season'])
                round_num = int(race['round'])
                race_name = race['raceName']
                date = race.get('date', '')
                
                cursor.execute('''
                    INSERT OR REPLACE INTO races (race_id, season, round, race_name, date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (race_id, season_num, round_num, race_name, date))
                
                qualifying_results = race.get('QualifyingResults', [])
                for res in qualifying_results:
                    driver = res.get('Driver', {})
                    driver_id = driver['driverId']
                    given_name = driver.get('givenName', '')
                    family_name = driver.get('familyName', '')
                    code = driver.get('code', '')
                    perm_num = driver.get('permanentNumber', '')
                    nationality = driver.get('nationality', '')
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO drivers (driver_id, given_name, family_name, code, permanent_number, nationality)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (driver_id, given_name, family_name, code, perm_num, nationality))
                    
                    constructor = res.get('Constructor', {})
                    const_id = constructor.get('constructorId', '')
                    const_name = constructor.get('name', '')
                    
                    position = int(res.get('position', 99))
                    q1 = res.get('Q1', '')
                    q2 = res.get('Q2', '')
                    q3 = res.get('Q3', '')
                    
                    result_id = f"{race_id}_{driver_id}"
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO results (result_id, race_id, driver_id, constructor_id, constructor_name, position, q1, q2, q3)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (result_id, race_id, driver_id, const_id, const_name, position, q1, q2, q3))
            
            # Increase offset by the number of results returned (or standard limit)
            offset += limit
            # Give a tiny pause to avoid hitting rate limits
            time.sleep(0.5)
            
        conn.commit()
        conn.close()
        print(f"Successfully saved season {season} data.")
        return True
    except Exception as e:
        print(f"Error processing season {season}: {e}")
        return False

def main():
    init_db()
    current_year = time.localtime().tm_year
    # Fetch from 2021 to current year
    for year in range(2021, current_year + 1):
        success = fetch_and_store_season(year)
        if not success:
            # Try once more with delay
            time.sleep(2)
            fetch_and_store_season(year)
        time.sleep(1) # Be a good citizen

if __name__ == '__main__':
    main()

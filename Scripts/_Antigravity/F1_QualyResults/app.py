from flask import Flask, jsonify, request, render_template
import sqlite3

app = Flask(__name__)
DB_PATH = 'qualifying.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/drivers')
def get_drivers():
    conn = get_db_connection()
    # Get all drivers along with their most common/recent constructor
    query = '''
        SELECT d.driver_id, d.given_name, d.family_name, d.code, d.permanent_number, d.nationality,
               r.constructor_name, COUNT(r.constructor_name) as freq
        FROM drivers d
        JOIN results r ON d.driver_id = r.driver_id
        GROUP BY d.driver_id
        ORDER BY d.family_name ASC
    '''
    rows = conn.execute(query).fetchall()
    conn.close()
    
    drivers = []
    for r in rows:
        drivers.append({
            'driver_id': r['driver_id'],
            'given_name': r['given_name'],
            'family_name': r['family_name'],
            'code': r['code'],
            'permanent_number': r['permanent_number'],
            'nationality': r['nationality'],
            'team': r['constructor_name']
        })
    return jsonify(drivers)

@app.route('/api/results')
def get_results():
    driver_ids = request.args.get('drivers', '').split(',')
    seasons = request.args.get('seasons', '').split(',')
    
    # Filter empty items
    driver_ids = [d for d in driver_ids if d]
    seasons = [s for s in seasons if s]
    
    if not driver_ids:
        return jsonify([])
    
    conn = get_db_connection()
    
    # Base query
    query = '''
        SELECT r.season, r.round, r.race_name, r.date,
               res.driver_id, res.constructor_name, res.position, res.q1, res.q2, res.q3,
               d.given_name, d.family_name, d.code
        FROM results res
        JOIN races r ON res.race_id = r.race_id
        JOIN drivers d ON res.driver_id = d.driver_id
        WHERE res.driver_id IN ({})
    '''.format(','.join(['?'] * len(driver_ids)))
    
    params = list(driver_ids)
    
    if seasons:
        query += ' AND r.season IN ({})'.format(','.join(['?'] * len(seasons)))
        params.extend(seasons)
        
    query += ' ORDER BY r.season ASC, r.round ASC'
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    results = []
    for r in rows:
        results.append({
            'season': r['season'],
            'round': r['round'],
            'race_name': r['race_name'],
            'date': r['date'],
            'driver_id': r['driver_id'],
            'driver_name': f"{r['given_name']} {r['family_name']}",
            'driver_code': r['code'],
            'constructor_name': r['constructor_name'],
            'position': r['position'],
            'q1': r['q1'],
            'q2': r['q2'],
            'q3': r['q3']
        })
        
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

import json
import os
import uuid

DB_PATH = 'safes.json'

def load_safes():
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_safes(safes):
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(safes, f, indent=4)

def add_safe(name, path, safe_type, preferred_letter):
    safes = load_safes()
    new_safe = {
        'id': str(uuid.uuid4()),
        'name': name,
        'path': path,
        'type': safe_type,
        'preferred_letter': preferred_letter.upper() if preferred_letter else ''
    }
    safes.append(new_safe)
    save_safes(safes)
    return new_safe

def edit_safe(safe_id, name, path, safe_type, preferred_letter):
    safes = load_safes()
    for safe in safes:
        if safe['id'] == safe_id:
            safe['name'] = name
            safe['path'] = path
            safe['type'] = safe_type
            safe['preferred_letter'] = preferred_letter.upper() if preferred_letter else ''
            break
    save_safes(safes)

def delete_safe(safe_id):
    safes = load_safes()
    safes = [s for s in safes if s['id'] != safe_id]
    save_safes(safes)

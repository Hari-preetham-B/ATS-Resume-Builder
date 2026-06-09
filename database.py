import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'database.json')

def read_db():
    if not os.path.exists(DB_PATH):
        # Create default structure
        write_db({'users': [], 'resumes': []})
    with open(DB_PATH, 'r') as f:
        return json.load(f)

def write_db(data):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, 'w') as f:
        json.dump(data, f, indent=2)
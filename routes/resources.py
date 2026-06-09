from flask import Blueprint, request, jsonify, session
from database import read_db, write_db
import uuid
from datetime import datetime
import os
import requests

resources_bp = Blueprint('resources', __name__)

# ========== GET all resume examples ==========
@resources_bp.route('/resume-examples', methods=['GET'])
def get_resume_examples():
    db = read_db()
    examples = db.get('resume_examples', [])
    examples.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return jsonify(examples), 200

# ========== ADD a new resume example ==========
@resources_bp.route('/resume-examples', methods=['POST'])
def add_resume_example():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    required = ['title', 'industry', 'image_url', 'description']
    for field in required:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    new_example = {
        'id': str(uuid.uuid4()),
        'title': data['title'],
        'industry': data['industry'],
        'image_url': data['image_url'],
        'description': data.get('description', ''),
        'created_at': datetime.now().isoformat()
    }
    db = read_db()
    if 'resume_examples' not in db:
        db['resume_examples'] = []
    db['resume_examples'].append(new_example)
    write_db(db)
    return jsonify(new_example), 201

# ========== DELETE a resume example ==========
@resources_bp.route('/resume-examples/<example_id>', methods=['DELETE'])
def delete_resume_example(example_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    db = read_db()
    examples = db.get('resume_examples', [])
    new_examples = [e for e in examples if e['id'] != example_id]
    if len(new_examples) == len(examples):
        return jsonify({'error': 'Not found'}), 404
    db['resume_examples'] = new_examples
    write_db(db)
    return jsonify({'message': 'Deleted'}), 200

# ========== YOUTUBE SEARCH (using your API key) ==========
@resources_bp.route('/youtube-search', methods=['GET'])
def youtube_search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    # Get API key from environment variable (secure)
    youtube_api_key = os.getenv('YOUTUBE_API_KEY')
    if not youtube_api_key:
        # Fallback for testing – replace with your actual key or remove after testing
        youtube_api_key = 'AIzaSyCXbm9n6AI4PBEvuTVobMRgADSzfV7uLQ4'
        print("⚠️ Using fallback YouTube API key. Set YOUTUBE_API_KEY in .env for production.")

    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=6&q={query}&type=video&key={youtube_api_key}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return jsonify({'error': 'YouTube API error', 'details': resp.text}), resp.status_code
        data = resp.json()
        items = data.get('items', [])
        videos = [{'id': item['id']['videoId'], 'title': item['snippet']['title']} for item in items]
        return jsonify(videos), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
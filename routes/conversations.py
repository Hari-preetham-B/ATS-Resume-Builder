from flask import Blueprint, request, jsonify, session
from database import read_db, write_db
from datetime import datetime

conv_bp = Blueprint('conversations', __name__)

@conv_bp.route('/list', methods=['GET'])
def list_conversations():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    db = read_db()
    user_convs = db.get('conversations', {}).get(session['user_id'], [])
    # Return list of { id, title, updated_at }
    result = [{'id': c['id'], 'title': c['title'], 'updated_at': c['updated_at']} for c in user_convs]
    result.sort(key=lambda x: x['updated_at'], reverse=True)
    return jsonify(result)

@conv_bp.route('/get/<conv_id>', methods=['GET'])
def get_conversation(conv_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    db = read_db()
    convs = db.get('conversations', {}).get(session['user_id'], [])
    conv = next((c for c in convs if c['id'] == conv_id), None)
    if not conv:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(conv)

@conv_bp.route('/save', methods=['POST'])
def save_conversation():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    conv_id = data.get('id')
    title = data.get('title', 'New Conversation')
    messages = data.get('messages', [])
    updated_at = datetime.now().isoformat()
    db = read_db()
    if 'conversations' not in db:
        db['conversations'] = {}
    if session['user_id'] not in db['conversations']:
        db['conversations'][session['user_id']] = []
    convs = db['conversations'][session['user_id']]
    if conv_id:
        # update existing
        for i, c in enumerate(convs):
            if c['id'] == conv_id:
                convs[i]['messages'] = messages
                convs[i]['updated_at'] = updated_at
                if title:
                    convs[i]['title'] = title
                break
    else:
        # create new
        new_id = f"conv_{datetime.now().timestamp()}_{session['user_id'][-6:]}"
        convs.append({
            'id': new_id,
            'title': title,
            'messages': messages,
            'created_at': datetime.now().isoformat(),
            'updated_at': updated_at
        })
        conv_id = new_id
    write_db(db)
    return jsonify({'id': conv_id, 'message': 'Saved'})

@conv_bp.route('/delete/<conv_id>', methods=['DELETE'])
def delete_conversation(conv_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    db = read_db()
    convs = db.get('conversations', {}).get(session['user_id'], [])
    new_convs = [c for c in convs if c['id'] != conv_id]
    if len(new_convs) == len(convs):
        return jsonify({'error': 'Not found'}), 404
    db['conversations'][session['user_id']] = new_convs
    write_db(db)
    return jsonify({'message': 'Deleted'})
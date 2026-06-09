from flask import Blueprint, request, jsonify, session
from database import read_db, write_db
import uuid
from datetime import datetime

resume_bp = Blueprint('resume', __name__)

def is_authenticated():
    return 'user_id' in session

@resume_bp.route('/save', methods=['POST'])
def save_resume():
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    resume_id = data.get('id')
    title = data.get('title', 'Untitled Resume')
    resume_data = data.get('data', {})
    score = data.get('score', 0)

    db = read_db()
    user_id = session['user_id']

    if resume_id:
        # Update existing
        for i, r in enumerate(db['resumes']):
            if r['id'] == resume_id and r['userId'] == user_id:
                db['resumes'][i]['title'] = title
                db['resumes'][i]['data'] = resume_data
                db['resumes'][i]['score'] = score
                db['resumes'][i]['updatedAt'] = datetime.now().isoformat()
                write_db(db)
                return jsonify({'message': 'Resume updated', 'resume': db['resumes'][i]}), 200
        return jsonify({'error': 'Resume not found'}), 404
    else:
        # Create new
        new_resume = {
            'id': 'res_' + str(uuid.uuid4()).replace('-', '')[:12],
            'userId': user_id,
            'title': title,
            'data': resume_data,
            'score': score,
            'downloads': 0,
            'createdAt': datetime.now().isoformat(),
            'updatedAt': datetime.now().isoformat()
        }
        db['resumes'].append(new_resume)
        write_db(db)
        return jsonify({'message': 'Resume saved', 'resume': new_resume}), 201

@resume_bp.route('/list', methods=['GET'])
def list_resumes():
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401

    db = read_db()
    user_resumes = [r for r in db['resumes'] if r['userId'] == session['user_id']]
    user_resumes.sort(key=lambda x: x['updatedAt'], reverse=True)
    return jsonify(user_resumes), 200

@resume_bp.route('/<resume_id>', methods=['GET'])
def get_resume(resume_id):
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401

    db = read_db()
    resume = next((r for r in db['resumes'] if r['id'] == resume_id and r['userId'] == session['user_id']), None)
    if not resume:
        return jsonify({'error': 'Resume not found'}), 404
    return jsonify(resume), 200

@resume_bp.route('/download/<resume_id>', methods=['POST'])
def increment_download(resume_id):
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401

    db = read_db()
    for r in db['resumes']:
        if r['id'] == resume_id and r['userId'] == session['user_id']:
            r['downloads'] = r.get('downloads', 0) + 1
            write_db(db)
            return jsonify({'message': 'Download count updated'}), 200
    return jsonify({'error': 'Resume not found'}), 404

@resume_bp.route('/<resume_id>', methods=['DELETE'])
def delete_resume(resume_id):
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401

    db = read_db()
    original_len = len(db['resumes'])
    db['resumes'] = [r for r in db['resumes'] if not (r['id'] == resume_id and r['userId'] == session['user_id'])]
    if len(db['resumes']) < original_len:
        write_db(db)
        return jsonify({'message': 'Resume deleted'}), 200
    return jsonify({'error': 'Resume not found'}), 404
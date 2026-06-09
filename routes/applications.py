from flask import Blueprint, request, jsonify, session
from database import read_db, write_db
from datetime import datetime
import uuid

applications_bp = Blueprint('applications', __name__)

def get_user_apps():
    db = read_db()
    if 'applications' not in db:
        db['applications'] = []
        write_db(db)
    apps = [a for a in db['applications'] if a.get('user_id') == session['user_id']]
    # sort by date_applied desc (newest first)
    apps.sort(key=lambda x: x.get('date_applied', ''), reverse=True)
    return apps

@applications_bp.route('/', methods=['GET'])
def get_applications():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(get_user_apps()), 200
@applications_bp.route('/<app_id>', methods=['GET'])
def get_application(app_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    db = read_db()
    apps = db.get('applications', [])
    for app in apps:
        if app['id'] == app_id and app['user_id'] == session['user_id']:
            return jsonify(app), 200
    return jsonify({'error': 'Application not found'}), 404

@applications_bp.route('/', methods=['POST'])
def add_application():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    required = ['job_title', 'company', 'status']
    for field in required:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    new_app = {
        'id': str(uuid.uuid4()),
        'user_id': session['user_id'],
        'job_title': data['job_title'],
        'company': data['company'],
        'location': data.get('location', ''),
        'status': data['status'],
        'resume_id': data.get('resume_id', ''),
        'date_applied': data.get('date_applied', datetime.now().isoformat()),
        'notes': data.get('notes', ''),
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    db = read_db()
    if 'applications' not in db:
        db['applications'] = []
    db['applications'].append(new_app)
    write_db(db)
    return jsonify(new_app), 201

@applications_bp.route('/<app_id>', methods=['PUT'])
def update_application(app_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    db = read_db()
    apps = db.get('applications', [])
    for app in apps:
        if app['id'] == app_id and app['user_id'] == session['user_id']:
            # update allowed fields
            app['job_title'] = data.get('job_title', app['job_title'])
            app['company'] = data.get('company', app['company'])
            app['location'] = data.get('location', app['location'])
            app['status'] = data.get('status', app['status'])
            app['resume_id'] = data.get('resume_id', app['resume_id'])
            app['date_applied'] = data.get('date_applied', app['date_applied'])
            app['notes'] = data.get('notes', app['notes'])
            app['updated_at'] = datetime.now().isoformat()
            write_db(db)
            return jsonify(app), 200
    return jsonify({'error': 'Application not found'}), 404

@applications_bp.route('/<app_id>', methods=['DELETE'])
def delete_application(app_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    db = read_db()
    apps = db.get('applications', [])
    new_apps = [a for a in apps if not (a['id'] == app_id and a['user_id'] == session['user_id'])]
    if len(new_apps) == len(apps):
        return jsonify({'error': 'Application not found'}), 404
    db['applications'] = new_apps
    write_db(db)
    return jsonify({'message': 'Deleted'}), 200
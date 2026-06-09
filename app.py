from flask import Flask, send_from_directory, jsonify, session
from flask_cors import CORS
from flask_session import Session   # <-- ADD THIS IMPORT
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


from routes.auth import auth_bp
from routes.resume import resume_bp
from routes.ai import ai_bp
from database import read_db

app = Flask(__name__, static_folder='static')
from routes.conversations import conv_bp
app.register_blueprint(conv_bp, url_prefix='/api/conversations')

from routes.applications import applications_bp
app.register_blueprint(applications_bp, url_prefix='/api/applications')

from routes.resources import resources_bp
app.register_blueprint(resources_bp, url_prefix='/api/resources')

from routes.mock_interview import mock_bp
app.register_blueprint(mock_bp, url_prefix='/api/mock-interview')

# Secret key (must be set)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

# Session configuration
app.config['SESSION_TYPE'] = 'filesystem'          # <-- ADD THIS (required)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_COOKIE_MAX_AGE'] = None

# Initialize the session extension
Session(app)   # <-- ADD THIS (MISSING)

CORS(app, supports_credentials=True, origins='http://localhost:5000')

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(resume_bp, url_prefix='/api/resume')
app.register_blueprint(ai_bp, url_prefix='/api/ai')

# Serve static files
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/api/user/stats', methods=['GET'])
def user_stats():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    db = read_db()
    user_id = session['user_id']
    user_resumes = [r for r in db.get('resumes', []) if r.get('userId') == user_id]
    total_resumes = len(user_resumes)
    total_downloads = sum(r.get('downloads', 0) for r in user_resumes)
    total_score = sum(r.get('score', 0) for r in user_resumes)
    ats_avg = round(total_score / total_resumes) if total_resumes > 0 else 0
    return jsonify({
        'resumesCreated': total_resumes,
        'downloads': total_downloads,
        'profileViews': total_resumes * 3,
        'atsScoreAvg': ats_avg
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
from flask import Blueprint, request, jsonify, session
import bcrypt
import uuid
from datetime import datetime
from database import read_db, write_db
import random
#from utils.email import send_otp_email, send_reset_email
from utils.mail_helper import send_otp_email, send_reset_email

auth_bp = Blueprint('auth', __name__)

def get_user_safe(user):
    safe = user.copy()
    safe.pop('password', None)
    safe.pop('resetToken', None)
    safe.pop('resetTokenExpiry', None)
    safe.pop('otp', None)
    safe.pop('otp_expiry', None)
    safe.pop('reset_token', None)
    safe.pop('reset_token_expiry', None)
    # Keep all other fields including skills, experiences, educations, projects
    return safe

@auth_bp.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('fullName', '')
        phone = data.get('phone', '')
        linkedin = data.get('linkedin', '')
        github = data.get('github', '')

        if not username or not email or not password:
            return jsonify({'error': 'All fields are required'}), 400

        db = read_db()
        for u in db['users']:
            if u['username'] == username or u['email'] == email:
                return jsonify({'error': 'User already exists'}), 409

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_user = {
            'id': 'user_' + str(uuid.uuid4()).replace('-', '')[:12],
            'username': username,
            'email': email,
            'fullName': full_name,
            'phone': phone,
            'linkedin': linkedin,
            'github': github,
            'password': hashed,
            'createdAt': datetime.now().isoformat(),
            # Initialize structured fields as empty arrays
            'skills': [],
            'experiences': [],
            'educations': [],
            'projects': []
        }
        db['users'].append(new_user)
        write_db(db)

        return jsonify({'message': 'Registered successfully'}), 201
    except Exception as e:
        print('Signup error:', e)
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    print("🔔 forgot_password endpoint called")
    data = request.json
    email = data.get('email')
    print(f"   Email received: {email}")

    if not email:
        return jsonify({'error': 'Email required'}), 400

    db = read_db()
    user = next((u for u in db['users'] if u['email'] == email), None)
    if not user:
        print("   User not found – user is not registered")
        return jsonify({'error': 'This email is not registered. Please sign up first.'}), 200

    token = str(uuid.uuid4()).replace('-', '')
    user['reset_token'] = token
    user['reset_token_expiry'] = datetime.now().timestamp() + 3600
    write_db(db)
    print(f"   Token generated: {token}")
    print(f"\n🔐 RESET LINK: http://localhost:5000/reset-password.html?token={token}\n")

    # Send email
    result = send_reset_email(email, token)
    print(f"   send_reset_email returned: {result}")

    return jsonify({'message': 'Reset link sent to your email'}), 200

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    token = data.get('token')
    new_password = data.get('newPassword')
    if not token or not new_password:
        return jsonify({'error': 'Token and new password required'}), 400

    db = read_db()
    user = None
    for u in db['users']:
        if u.get('reset_token') == token and u.get('reset_token_expiry', 0) > datetime.now().timestamp():
            user = u
            break

    if not user:
        return jsonify({'error': 'Invalid or expired token'}), 400

    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user['password'] = hashed
    user.pop('reset_token', None)
    user.pop('reset_token_expiry', None)
    write_db(db)

    return jsonify({'message': 'Password updated successfully'}), 200

@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.json
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Email required'}), 400

    db = read_db()
    user = next((u for u in db['users'] if u['email'] == email), None)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    otp = str(random.randint(100000, 999999))
    user['otp'] = otp
    user['otp_expiry'] = datetime.now().timestamp() + 300
    write_db(db)

    # send_otp_email(email, otp)  # Uncomment when email is configured
    print(f"OTP for {email}: {otp}")
    return jsonify({'message': 'OTP sent'}), 200

@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    username_or_email = data.get('username') or data.get('email')
    otp = data.get('otp')
    if not username_or_email or not otp:
        return jsonify({'error': 'Username/Email and OTP required'}), 400

    db = read_db()
    user = next((u for u in db['users'] if u['username'] == username_or_email or u['email'] == username_or_email), None)
    if not user or user.get('otp') != otp or user.get('otp_expiry', 0) < datetime.now().timestamp():
        return jsonify({'error': 'Invalid or expired OTP'}), 401

    user.pop('otp', None)
    user.pop('otp_expiry', None)
    write_db(db)
    session['user_id'] = user['id']
    session['username'] = user['username']
    return jsonify({'message': 'Verification successful', 'user': get_user_safe(user)}), 200

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        username_or_email = data.get('username')
        password = data.get('password')

        if not username_or_email or not password:
            return jsonify({'error': 'Username/Email and password required'}), 400

        db = read_db()
        user = None
        for u in db['users']:
            if u['username'] == username_or_email or u['email'] == username_or_email:
                user = u
                break

        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401

        if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({'error': 'Invalid credentials'}), 401

        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({'message': 'Login successful', 'user': get_user_safe(user)}), 200
    except Exception as e:
        print('Login error:', e)
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/user', methods=['GET'])
def get_user():
    try:
        if 'user_id' not in session:
            return jsonify({'isLoggedIn': False}), 200

        db = read_db()
        user = next((u for u in db['users'] if u['id'] == session['user_id']), None)
        if not user:
            session.clear()
            return jsonify({'isLoggedIn': False}), 200

        # Ensure array fields exist for older users (who registered before this update)
        if 'skills' not in user:
            user['skills'] = []
        if 'experiences' not in user:
            user['experiences'] = []
        if 'educations' not in user:
            user['educations'] = []
        if 'projects' not in user:
            user['projects'] = []

        return jsonify({'isLoggedIn': True, 'user': get_user_safe(user)}), 200
    except Exception as e:
        print('User check error:', e)
        return jsonify({'isLoggedIn': False}), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'}), 200

@auth_bp.route('/update-profile', methods=['PUT'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    db = read_db()
    user = next((u for u in db['users'] if u['id'] == session['user_id']), None)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Basic fields
    if 'fullName' in data:
        user['fullName'] = data['fullName']
    if 'email' in data:
        user['email'] = data['email']
    if 'phone' in data:
        user['phone'] = data['phone']
    if 'profileImage' in data:
        user['profileImage'] = data['profileImage']
    if 'linkedin' in data:
        user['linkedin'] = data['linkedin']
    if 'github' in data:
        user['github'] = data['github']
    if 'summary' in data:
        user['summary'] = data['summary']

    # Array fields (plural) – these are what the new profile page sends
    if 'skills' in data:
        user['skills'] = data['skills']
    if 'experiences' in data:
        user['experiences'] = data['experiences']
    if 'educations' in data:
        user['educations'] = data['educations']
    if 'projects' in data:
        user['projects'] = data['projects']

    # Also keep old singular fields for backward compatibility (if needed)
    if 'experience' in data and 'experiences' not in data:
        user['experience'] = data['experience']
    if 'education' in data and 'educations' not in data:
        user['education'] = data['education']

    write_db(db)
    return jsonify({'message': 'Profile updated', 'user': get_user_safe(user)}), 200
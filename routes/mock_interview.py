from flask import Blueprint, request, jsonify, session
from database import read_db, write_db
from datetime import datetime
import uuid
import os
import tempfile
import subprocess
import requests
import json
import base64
import re
import traceback
import whisper
from collections import defaultdict

mock_bp = Blueprint('mock_interview', __name__)

# ========== TRACK ASKED QUESTIONS PER USER ==========
asked_questions = defaultdict(list)

# ========== MOCK MODE (for testing without transcription) ==========
MOCK_WHISPER = os.getenv('MOCK_WHISPER', 'false').lower() == 'true'

# ========== HELPER: OpenRouter Chat ==========
def call_openrouter(messages, max_tokens=500, temperature=0.9):
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set")
        return None
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    payload = {
        'model': 'openai/gpt-4o-mini',
        'messages': messages,
        'max_tokens': max_tokens,
        'temperature': temperature
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            print(f"❌ OpenRouter chat error: {resp.status_code} - {resp.text[:200]}")
            return None
        data = resp.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        print(f"❌ OpenRouter call failed: {e}")
        return None

# ========== RESUME VALIDATION ENDPOINT (FLEXIBLE – EXPERIENCE OPTIONAL) ==========
@mock_bp.route('/validate-resume', methods=['POST'])
def validate_resume():
    """AI-powered resume validation - accepts student/fresher resumes without experience"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    resume_text = data.get('resume_text', '')
    
    if not resume_text:
        return jsonify({
            'is_valid': False,
            'message': 'Please paste your resume content.'
        }), 200
    
    if len(resume_text) < 100:
        return jsonify({
            'is_valid': False,
            'message': f'Resume text is too short ({len(resume_text)} characters). A valid resume should have at least 100 characters.'
        }), 200
    
    # Flexible validation: For students/freshers, experience is NOT mandatory.
    # Require at least 2 of: Skills, Projects, Education, Experience (if any)
    text_lower = resume_text.lower()
    has_skills = any(w in text_lower for w in ['skill', 'technologies', 'technical', 'programming languages'])
    has_projects = 'project' in text_lower
    has_education = any(w in text_lower for w in ['education', 'degree', 'university', 'college', 'bachelor', 'master', 'academic', 'school'])
    has_experience = any(w in text_lower for w in ['experience', 'work', 'employment', 'job', 'internship'])
    
    valid_sections = sum([has_skills, has_projects, has_education, has_experience])
    
    if valid_sections < 2:
        missing = []
        if not has_skills: missing.append('Skills')
        if not has_projects: missing.append('Projects')
        if not has_education: missing.append('Education')
        return jsonify({
            'is_valid': False,
            'message': f'Missing key sections: {", ".join(missing)}. Please include at least Skills and Projects (or Education).',
            'detected_sections': ', '.join([s for s in ['Skills', 'Projects', 'Education', 'Experience'] if locals().get(f'has_{s.lower()}', False)])
        }), 200
    
    if not has_projects and not has_skills:
        return jsonify({
            'is_valid': False,
            'message': 'Resume should include either Projects or Skills section.',
            'detected_sections': ''
        }), 200
    
    # Try AI-based validation with relaxed criteria
    prompt = f"""You are a resume validator for a mock interview platform. Determine if the following text is a valid resume.

A valid resume can be for a student or professional. It MUST have at least TWO of these: Skills, Projects, Education. Work experience is optional.

Text to analyze:
{resume_text[:2000]}

Return ONLY a JSON object with:
{{"is_valid": true/false, "message": "brief explanation (max 100 chars)", "detected_sections": "comma separated list of sections found"}}"""

    content = call_openrouter([{'role': 'user', 'content': prompt}], max_tokens=200, temperature=0.3)
    
    if content:
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group())
                detected = result.get('detected_sections', '')
                return jsonify({
                    'is_valid': result.get('is_valid', True),
                    'message': result.get('message', 'Resume validation complete'),
                    'detected_sections': detected
                }), 200
            except:
                pass
    
    # Fallback validation
    detected = []
    if has_skills: detected.append('Skills')
    if has_projects: detected.append('Projects')
    if has_education: detected.append('Education')
    if has_experience: detected.append('Experience')
    
    return jsonify({
        'is_valid': True,
        'message': '✅ Resume validated successfully!',
        'detected_sections': ', '.join(detected)
    }), 200

# ========== IMPROVED FALLBACK QUESTIONS (PURELY RESUME-BASED) ==========
def generate_fallback_questions(resume_text):
    """Generate questions based ONLY on specific resume content (projects, skills, experience)"""
    # Extract sections
    skills = []
    if "Skills:" in resume_text:
        skills_section = resume_text.split("Skills:")[1].split("\n")[0]
        skills = [s.strip() for s in skills_section.split(",") if s.strip()]
    
    projects = []
    if "Projects:" in resume_text:
        proj_section = resume_text.split("Projects:")[1].split("\n")[0]
        projects = [p.strip() for p in proj_section.split(",") if p.strip()]
    
    experience = []
    if "Experience:" in resume_text:
        exp_section = resume_text.split("Experience:")[1].split("\n")[0]
        experience = [e.strip() for e in exp_section.split(",") if e.strip()]
    
    questions = []
    
    # Prefer projects first
    if projects and len(projects) > 0:
        proj = projects[0]
        questions.append(f"Walk me through your project '{proj}'. What was your specific role and what technologies did you use?")
    if len(projects) > 1:
        proj2 = projects[1]
        questions.append(f"Describe a challenge you faced while building '{proj2}' and how you solved it.")
    
    # If not enough projects, use skills
    if len(questions) < 2 and skills:
        skill = skills[0]
        questions.append(f"In your resume, you mention {skill}. Can you give an example of a real-world problem you solved using {skill}?")
    
    # If still not enough, use education or achievements
    if len(questions) < 2:
        # Look for hackathon or achievement keywords
        if 'hackathon' in resume_text.lower():
            questions.append("You participated in hackathons. Tell me about one hackathon project and your contribution.")
        elif 'certification' in resume_text.lower():
            questions.append("Which certification from your resume has been most valuable and why?")
        else:
            questions.append("What specific project from your resume are you most proud of and why?")
            questions.append("Which technical skill from your resume do you consider your strongest and how have you applied it?")
    
    return questions[:2]

# ========== IMPROVED QUESTION GENERATION (STRICTLY FROM RESUME) ==========
def generate_two_questions(resume_text):
    """Generate 2 UNIQUE interview questions based ONLY on specific resume content (no generic)"""
    user_id = session.get('user_id', 'default')
    prev_questions = asked_questions.get(user_id, [])
    prev_questions_text = "\n".join([f"- {q}" for q in prev_questions[-4:]]) if prev_questions else "None yet"
    
    # Truncate resume to avoid token overload
    resume_preview = resume_text[:2500]
    
    prompt = f"""You are an expert technical interviewer. Based STRICTLY on the candidate's resume below, generate 2 UNIQUE interview questions.

CRITICAL RULES:
- DO NOT ask generic questions like "Tell me about yourself" or "Why do you want this job".
- DO NOT use any job title unless it's explicitly mentioned in the resume.
- Questions MUST reference SPECIFIC projects (by name), SPECIFIC technical skills, or SPECIFIC achievements mentioned in the resume.
- Each question should target a different part of the resume (e.g., one about a project, one about a skill or hackathon).
- DO NOT repeat these previously asked questions:
{prev_questions_text}

Resume:
{resume_preview}

Return ONLY a JSON array of two strings. Example format: ["In your project 'Scrap finder', what was your role and what technologies did you use?", "You listed Python as a skill. Describe a time you used Python to solve a real problem."]"""

    content = call_openrouter([{'role': 'user', 'content': prompt}], max_tokens=400, temperature=0.8)
    
    if content:
        match = re.search(r'\[\s*".*"\s*,\s*".*"\s*\]', content, re.DOTALL)
        if match:
            try:
                questions = json.loads(match.group())
                if isinstance(questions, list) and len(questions) == 2:
                    # Ensure both questions are non-empty and not generic
                    generic_indicators = ['tell me about yourself', 'why do you want', 'what are your strengths', 'introduce yourself']
                    if not any(any(ind in q.lower() for ind in generic_indicators) for q in questions):
                        asked_questions[user_id].extend(questions)
                        return questions
            except:
                pass
    
    print("⚠️ AI question generation failed, using fallback (resume-based)")
    return generate_fallback_questions(resume_text)

# ========== IMPROVED ANSWER EVALUATION (BASED ON RESUME RELEVANCE) ==========
def evaluate_answer(question, answer_text, resume_text):
    """Evaluate answer based on how well it references resume content, specificity, and coherence"""
    prompt = f"""You are an expert interview coach. Evaluate the candidate's answer based ONLY on their resume content.

Resume:
{resume_text[:2000]}

Question asked: {question}

Candidate's answer: {answer_text}

Return a JSON object with:
- "score": integer from 0 to 100 (0 = completely irrelevant, 100 = excellent, detailed, resume‑grounded answer)
- "feedback": short 2‑sentence constructive feedback
- "tips": list of two specific tips to improve

Scoring guidelines:
- 0-30: Answer is generic, doesn't reference the resume, or is off‑topic.
- 31-60: Mentions resume but lacks specifics or depth.
- 61-80: Good, uses specific resume details (project name, skill, experience) and explains reasonably.
- 81-100: Excellent, deeply relevant, shows clear understanding, uses concrete examples from resume.

Return ONLY valid JSON. No extra text."""

    content = call_openrouter([{'role': 'user', 'content': prompt}], max_tokens=350, temperature=0.4)
    
    if content:
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group())
                score = result.get('score', 70)
                score = max(0, min(100, score))
                return {
                    "score": score,
                    "feedback": result.get('feedback', 'Good effort, but try to be more specific to your resume.'),
                    "tips": result.get('tips', ['Mention specific projects from your resume', 'Quantify achievements when possible'])
                }
            except:
                pass
    
    # Fallback evaluation (simple keyword matching)
    resume_words = set(re.findall(r'\b\w+\b', resume_text.lower()))
    answer_words = set(re.findall(r'\b\w+\b', answer_text.lower()))
    overlap = len(resume_words.intersection(answer_words))
    total_unique = len(resume_words.union(answer_words))
    score = int((overlap / max(1, total_unique)) * 100) if total_unique > 0 else 30
    score = max(30, min(85, score))
    
    return {
        "score": score,
        "feedback": "Your answer touched on some relevant points. For better results, directly reference your resume projects or skills.",
        "tips": ["Use specific project names from your resume", "Explain your role and the technologies you used"]
    }

# ========== AUDIO TRANSCRIPTION - LOCAL WHISPER ==========
def transcribe_audio(audio_file_path):
    if MOCK_WHISPER:
        return "This is a simulated transcription for testing purposes. I have relevant experience and skills for this role."
    
    try:
        print("🎤 Loading Whisper model...")
        model = whisper.load_model("base")
        print(f"🎤 Transcribing audio file: {audio_file_path}")
        result = model.transcribe(audio_file_path, language="en")
        transcript = result["text"].strip()
        if not transcript:
            raise Exception("No speech detected in audio")
        print(f"✅ Transcription successful: {transcript[:100]}...")
        return transcript
    except Exception as e:
        print(f"❌ Local Whisper error: {e}")
        raise Exception(f"Transcription failed: {str(e)}")

def convert_video_to_audio(video_path):
    audio_path = video_path.replace('.webm', '.wav')
    cmd = ['ffmpeg', '-i', video_path, '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', audio_path, '-y']
    print(f"🔄 Converting video to audio...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        print(f"❌ FFmpeg error: {result.stderr}")
        raise Exception(f"FFmpeg conversion failed: {result.stderr}")
    return audio_path

def estimate_confidence(audio_path):
    try:
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.stdout.strip():
            duration = float(result.stdout.strip())
            return min(100, int((duration / 20.0) * 100))
    except:
        pass
    return 50

# ========== HELPER: GET USER RESUME FROM SAVED RESUMES ==========
def get_user_resume_content(user_id):
    db = read_db()
    resumes = [r for r in db.get('resumes', []) if r['userId'] == user_id]
    if not resumes:
        return None
    latest = sorted(resumes, key=lambda x: x.get('updatedAt', ''), reverse=True)[0]
    data = latest.get('data', {})
    parts = []
    if data.get('name'): parts.append(f"Name: {data['name']}")
    if data.get('summary'): parts.append(f"Summary: {data['summary']}")
    skills = data.get('skills')
    if skills:
        if isinstance(skills, list):
            parts.append(f"Skills: {', '.join(skills)}")
        else:
            parts.append(f"Skills: {skills}")
    if data.get('experience'): parts.append(f"Experience: {data['experience']}")
    if data.get('education'): parts.append(f"Education: {data['education']}")
    if data.get('projects'): parts.append(f"Projects: {data['projects']}")
    return "\n".join(parts)

# ========== ROUTES ==========

@mock_bp.route('/start-session', methods=['POST'])
def start_session():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    resume_text = data.get('resume_text', '')
    
    if not resume_text:
        resume_text = get_user_resume_content(session['user_id'])
    
    if not resume_text:
        return jsonify({'error': 'No resume found. Please paste your resume first.'}), 404

    try:
        questions = generate_two_questions(resume_text)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Extract and store resume sections for potential fallback
    skills = []
    projects = []
    if "Skills:" in resume_text:
        skills_section = resume_text.split("Skills:")[1].split("\n")[0]
        skills = [s.strip() for s in skills_section.split(",") if s.strip()]
    if "Projects:" in resume_text:
        proj_section = resume_text.split("Projects:")[1].split("\n")[0]
        projects = [p.strip() for p in proj_section.split(",") if p.strip()]

    db = read_db()
    session_id = str(uuid.uuid4())
    if 'mock_sessions' not in db:
        db['mock_sessions'] = []
    db['mock_sessions'].append({
        'id': session_id,
        'user_id': session['user_id'],
        'resume_text': resume_text,
        'resume_skills': skills,
        'resume_projects': projects,
        'questions': questions,
        'answers': [],
        'scores': [],
        'created_at': datetime.now().isoformat(),
        'status': 'in_progress'
    })
    write_db(db)
    return jsonify({'session_id': session_id, 'questions': questions}), 200

@mock_bp.route('/submit-answer', methods=['POST'])
def submit_answer():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    session_id = data.get('session_id')
    question_index = data.get('question_index')
    video_base64 = data.get('video', '')
    eye_contact = data.get('eye_contact', 50)
    text_answer = data.get('text_answer', '')
    
    temp_files = []
    
    try:
        if video_base64:
            # Save video
            if ',' in video_base64:
                video_base64 = video_base64.split(',')[1]
            video_data = base64.b64decode(video_base64)
            
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as vf:
                vf.write(video_data)
                video_path = vf.name
                temp_files.append(video_path)
            
            # Convert to audio
            audio_path = convert_video_to_audio(video_path)
            temp_files.append(audio_path)
            
            # Transcribe
            transcript = transcribe_audio(audio_path)
            confidence = estimate_confidence(audio_path)
        else:
            transcript = text_answer.strip()
            if not transcript:
                return jsonify({'error': 'No answer provided'}), 400
            confidence = 50
            eye_contact = 50
        
        # Load session
        db = read_db()
        sessions_list = db.get('mock_sessions', [])
        sess = next((s for s in sessions_list if s['id'] == session_id and s['user_id'] == session['user_id']), None)
        if not sess:
            return jsonify({'error': 'Session not found'}), 404
        
        # Evaluate
        question = sess['questions'][question_index]
        resume_text = sess.get('resume_text', '')
        
        evaluation = evaluate_answer(question, transcript, resume_text)
        content_score = evaluation.get('score', 50)
        # Final score: 70% content, 20% audio confidence, 10% eye contact (adjusted for students)
        final_score = int(content_score * 0.7 + confidence * 0.2 + eye_contact * 0.1)
        final_score = max(0, min(100, final_score))
        
        # Save answer
        sess['answers'].append({
            'question': question,
            'answer': transcript,
            'score': final_score,
            'feedback': evaluation.get('feedback', 'No feedback'),
            'tips': evaluation.get('tips', ['Practice more'])
        })
        sess['scores'].append(final_score)
        write_db(db)
        
        return jsonify({
            'score': final_score,
            'feedback': evaluation.get('feedback', 'Good effort'),
            'tips': evaluation.get('tips', ['Keep practicing']),
            'transcript': transcript
        }), 200
    
    except Exception as e:
        print(f"❌ ERROR: {traceback.format_exc()}")
        return jsonify({'error': f'Internal error: {str(e)}'}), 500
    
    finally:
        for f in temp_files:
            try:
                if os.path.exists(f):
                    os.unlink(f)
            except:
                pass

@mock_bp.route('/end-session', methods=['POST'])
def end_session():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    session_id = data.get('session_id')
    db = read_db()
    sessions_list = db.get('mock_sessions', [])
    for s in sessions_list:
        if s['id'] == session_id and s['user_id'] == session['user_id']:
            s['status'] = 'completed'
            s['ended_at'] = datetime.now().isoformat()
            write_db(db)
            return jsonify({'message': 'Session saved'}), 200
    return jsonify({'error': 'Session not found'}), 404
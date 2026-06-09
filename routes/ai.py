from flask import Blueprint, request, jsonify, session
import os
import random
import requests
import json
import re
from dotenv import load_dotenv

load_dotenv()

ai_bp = Blueprint('ai', __name__)

# ========== OLLAMA CONFIGURATION ==========
USE_LOCAL_AI = os.getenv('USE_LOCAL_AI', 'true').lower() == 'true'
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3.5:4b')
HAS_AI = USE_LOCAL_AI

def call_ollama(messages, max_tokens=250, temperature=0.7):
    """Call Ollama's native generate endpoint (hardcoded working URL)."""
    if not USE_LOCAL_AI:
        return None

    # Build plain text prompt from messages
    prompt_parts = []
    for msg in messages:
        role = msg['role']
        content = msg['content']
        if role == 'system':
            prompt_parts.append(f"System: {content}")
        elif role == 'user':
            prompt_parts.append(f"User: {content}")
        elif role == 'assistant':
            prompt_parts.append(f"Assistant: {content}")
    prompt = "\n".join(prompt_parts) + "\nAssistant:"

    url = "http://localhost:11434/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }

    print(f"🔵 Ollama request to {url} with model {OLLAMA_MODEL}")
    try:
        response = requests.post(url, json=payload, timeout=180)
        print(f"🟢 HTTP {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            content = data.get('response', '')
            if content and content.strip():
                print(f"✅ Response length: {len(content)} chars")
                return content
            else:
                print("⚠️ Empty content")
        else:
            print(f"❌ Error {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    return None

def is_authenticated():
    return 'user_id' in session

# ========== FALLBACK FUNCTIONS ==========
def fallback_ats_score(resume_text, job_desc):
    words = (resume_text + ' ' + job_desc).lower()
    keyword_pool = ['experience', 'project', 'team', 'lead', 'python', 'node', 'aws', 'sql', 'cloud', 'javascript', 'react', 'api', 'development']
    found = [kw for kw in keyword_pool if kw in words]
    score = max(20, min(80, round(len(found) / len(keyword_pool) * 80)))
    missing = [kw for kw in keyword_pool if kw not in found]
    return {
        'score': score,
        'missingKeywords': missing[:8],
        'strengths': ['Basic structure found', 'Contact information present'],
        'weaknesses': ['Limited ATS keywords', 'Add measurable achievements'],
        'suggestions': ['Use action verbs', 'Add quantifiable results', 'Match job description keywords']
    }

def fallback_chat(user_message, resume_content):
    responses = [
        "Your resume looks promising. Consider adding more quantifiable achievements.",
        "For interview prep, practice the STAR method (Situation, Task, Action, Result).",
        "To improve ATS score, include keywords from the job description."
    ]
    return random.choice(responses)  # No "unavailable" note

# ========== ATS SCORE ==========
@ai_bp.route('/ats-score', methods=['POST'])
def ats_score():
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    resume_content = data.get('resumeContent', '')
    job_description = data.get('jobDescription', '')

    if not resume_content or not job_description:
        return jsonify({'error': 'Resume content and job description are required'}), 400

    if not HAS_AI:
        return jsonify(fallback_ats_score(resume_content, job_description)), 200

    prompt = f"""Analyze this resume against the following job description. 
Return ONLY a JSON object with this structure:
{{"score": number (0-100), "missingKeywords": ["string"], "strengths": ["string"], "weaknesses": ["string"], "suggestions": ["string"]}}

Resume: {resume_content}

Job Description: {job_description}"""

    messages = [
        {"role": "system", "content": "You are a professional ATS optimizer. Return valid JSON only."},
        {"role": "user", "content": prompt}
    ]
    response = call_ollama(messages, max_tokens=500, temperature=0.3)
    if response:
        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                result = json.loads(match.group())
                return jsonify(result), 200
        except:
            pass
    return jsonify(fallback_ats_score(resume_content, job_description)), 200

# ========== CHATBOT ==========
@ai_bp.route('/chat', methods=['POST'])
def chat():
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    user_message = data.get('userMessage', '').strip()
    resume_content = data.get('resumeContent', '')
    system_prompt = data.get('systemPrompt', 
        "You are a professional career assistant and resume expert. Keep answers concise, practical, and helpful.")
    conversation_history = data.get('conversationHistory', [])

    if not user_message:
        return jsonify({'error': 'Message required'}), 400

    messages = [{"role": "system", "content": system_prompt}]
    if resume_content:
        messages.append({"role": "system", "content": f"User's resume: {resume_content[:2000]}"})
    for msg in conversation_history[-15:]:
        role = msg.get('role')
        content = msg.get('text') or msg.get('content')
        if role and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})

    if not HAS_AI:
        reply = fallback_chat(user_message, resume_content)
        return jsonify({'response': reply}), 200

    response = call_ollama(messages, max_tokens=250, temperature=0.7)
    if response:
        reply = response
    else:
        reply = fallback_chat(user_message, resume_content)
    return jsonify({'response': reply}), 200

# ========== HEALTH CHECK ==========
@ai_bp.route('/status', methods=['GET'])
def status():
    ollama_status = "unknown"
    try:
        test_resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        ollama_status = "connected" if test_resp.status_code == 200 else "error"
    except:
        ollama_status = "not_running"
    return jsonify({
        'ai_configured': HAS_AI,
        'provider': 'Ollama (Qwen3.5 4B)' if HAS_AI else 'None',
        'ollama_status': ollama_status,
        'model': OLLAMA_MODEL if HAS_AI else None
    }), 200
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('OPENROUTER_API_KEY')
print(f"API key loaded: {api_key[:10]}... (length {len(api_key)})")

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
payload = {
    'model': 'openai/gpt-4o-mini',
    'messages': [{'role': 'user', 'content': 'Say "Hello"'}],
    'max_tokens': 10
}

try:
    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
import os
import requests
import zipfile
import io

# Create models directory
os.makedirs('static/models', exist_ok=True)

# List of required files (tiny face detector + face landmark model)
files = {
    'tiny_face_detector_model-weights_manifest.json': 'https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/tiny_face_detector_model-weights_manifest.json',
    'tiny_face_detector_model-shard1': 'https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/tiny_face_detector_model-shard1',
    'face_landmark_68_model-weights_manifest.json': 'https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_landmark_68_model-weights_manifest.json',
    'face_landmark_68_model-shard1': 'https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_landmark_68_model-shard1'
}

for filename, url in files.items():
    print(f"Downloading {filename}...")
    r = requests.get(url)
    with open(f'static/models/{filename}', 'wb') as f:
        f.write(r.content)
print("✅ All model files downloaded to static/models/")
import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# This is the "List Models" endpoint
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

try:
    response = requests.get(url)
    if response.status_code == 200:
        models = response.json().get('models', [])
        print("--- I CAN SEE THESE MODELS ---")
        for m in models:
            # We only care about models that can 'generateContent'
            if 'generateContent' in m.get('supportedGenerationMethods', []):
                print(m.get('name'))
    else:
        print(f"FAILED: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
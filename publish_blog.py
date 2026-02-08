import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load keys (from .env locally, or Secrets on GitHub)
load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
WEBFLOW_TOKEN = os.getenv("WEBFLOW_API_TOKEN")
COLLECTION_ID = os.getenv("WEBFLOW_COLLECTION_ID")

def generate_blog_content():
    # Use the hour to vary the topic
    hour = datetime.utcnow().hour
    
    if hour < 10:
        category, angle = "Product", "Focus on Piggybank's features, the mini-app UI, and how to use it."
    elif hour < 16:
        category, angle = "Economy", "Focus on Web3 rewards, on-chain incentives, and the Propaganda economy."
    else:
        category, angle = "Ecosystem", "Focus on the Farcaster/Zora community and why Piggybank is the future of social apps."

    print(f"Generating {category} post...")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_KEY}"
    
    context = "Piggybank is a Web3 mini-app by 'Propaganda'. It lives on Farcaster and Zora. It's about on-chain social interactions."
    
    prompt = f"""
    {context}
    Write a high-quality blog post about: {angle}
    Return ONLY a JSON object:
    {{
      "title": "catchy title",
      "summary": "1-2 sentence summary",
      "html_content": "<h3>Headline</h3><p>Detailed paragraph about Piggybank...</p>",
      "category": "{category}"
    }}
    Do not use markdown code blocks like ```json.
    """
    
    response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
    
    if response.status_code == 200:
        raw_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        cleaned_text = raw_text.replace('```json', '').replace('```', '').strip()
        return json.loads(cleaned_text)
    else:
        raise Exception(f"Gemini Error: {response.text}")

def post_to_webflow(data):
    url = f"https://api.webflow.com/v2/collections/{COLLECTION_ID}/items"
    headers = {
        "Authorization": f"Bearer {WEBFLOW_TOKEN}",
        "accept-version": "2.0.0",
        "content-type": "application/json"
    }
    
    payload = {
        "fieldData": {
            "name": data['title'],
            "post-body": data['html_content'],
            "post-summary": data['summary'],
            "category": data['category'],
            "featured": False,   # ALWAYS OFF
            "_archived": False,
            "_draft": False      # ALWAYS LIVE
        }
    }
    
    print(f"Posting Live to Webflow...")
    res = requests.post(url, json=payload, headers=headers)
    if res.status_code in [200, 201, 202]:
        print(f"Success! {data['title']} is now LIVE on Webflow.")
    else:
        print(f"Webflow Error: {res.text}")

if __name__ == "__main__":
    try:
        content = generate_blog_content()
        post_to_webflow(content)
    except Exception as e:
        print(f"Failed: {e}")
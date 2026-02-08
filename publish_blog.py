import os
import requests
import json
from dotenv import load_dotenv

# Load keys from .env
load_dotenv()

# 1. Setup API Keys
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
WEBFLOW_TOKEN = os.getenv("WEBFLOW_API_TOKEN")
COLLECTION_ID = os.getenv("WEBFLOW_COLLECTION_ID")

def generate_blog_content():
    print("Asking Gemini to write the post...")
    
    # Direct URL using the model name from your list
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_KEY}"
    
    prompt = """
    Write a high-quality blog post about a trending tech topic. 
    Return the response in strictly valid JSON format with three keys: 
    "title", "summary", and "html_content". 
    Use <h3> and <p> tags for the html_content. 
    The summary should be 1-2 sentences.
    Do not use markdown (like # or **) inside the HTML content.
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        raw_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        # Clean potential markdown blocks
        cleaned_text = raw_text.replace('```json', '').replace('```', '').strip()
        return json.loads(cleaned_text)
    else:
        raise Exception(f"Gemini Error: {response.text}")

def post_to_webflow(blog_data):
    url = f"https://api.webflow.com/v2/collections/{COLLECTION_ID}/items"
    
    headers = {
        "Authorization": f"Bearer {WEBFLOW_TOKEN}",
        "accept-version": "2.0.0",
        "content-type": "application/json"
    }
    
    payload = {
        "fieldData": {
            "name": blog_data['title'],
            "post-body": blog_data['html_content'],
            "post-summary": blog_data['summary'],
            "_archived": False,
            "_draft": True 
        }
    }
    
    print(f"Sending to Webflow: {blog_data['title']}...")
    res = requests.post(url, json=payload, headers=headers)
    
    if res.status_code in [200, 201, 202]:
        print("Success! Your post is in Webflow Drafts.")
    else:
        print(f"Error from Webflow: {res.text}")

if __name__ == "__main__":
    try:
        blog_content = generate_blog_content()
        post_to_webflow(blog_content)
    except Exception as e:
        print(f"An error occurred: {e}")
import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 1. Setup API Keys
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
WEBFLOW_TOKEN = os.getenv("WEBFLOW_API_TOKEN")
COLLECTION_ID = os.getenv("WEBFLOW_COLLECTION_ID")

def generate_blog_content():
    # Get current hour to vary the topic
    hour = datetime.utcnow().hour
    
    # Logic to pick a category based on the time of day
    if hour < 10:
        category = "Product"
        angle = "Focus on features of Piggybank, the user interface, and how the mini-app works."
    elif hour < 16:
        category = "Economy"
        angle = "Focus on the Web3 economics, tokenization, or the financial incentives of using Piggybank."
    else:
        category = "Ecosystem"
        angle = "Focus on Propaganda (the creators), the Farcaster/Zora community, and the broader Web3 ecosystem."

    print(f"Asking Gemini to write a {category} post about Piggybank...")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_KEY}"
    
    # Context about Piggybank so Gemini doesn't guess
    context = """
    Context: Piggybank is a Web3 mini-app built by 'Propaganda'. 
    It is deeply integrated into the Farcaster and Zora ecosystems. 
    It's designed for the next generation of on-chain social and financial interaction.
    """

    prompt = f"""
    {context}
    Write a high-quality blog post for the category: {category}.
    Specific Angle: {angle}
    
    Return the response in strictly valid JSON format with these keys: 
    "title", "summary", "html_content", "category", "featured"
    
    Requirements:
    - html_content: Use <h3> and <p> tags. Mention 'Piggybank' and 'Propaganda'.
    - summary: 1-2 sentences.
    - category: Use exactly '{category}'.
    - featured: Return a boolean (true or false).
    - Do not use markdown like # or ** in the html_content.
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        raw_text = response.json()['candidates'][0]['content']['parts'][0]['text']
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
    
    # Mapped to your screenshot fields:
    payload = {
        "fieldData": {
            "name": blog_data['title'],
            "post-body": blog_data['html_content'],
            "post-summary": blog_data['summary'],
            "category": blog_data['category'],
            "featured": blog_data['featured'],
            # For the Image: We use a high-quality placeholder based on the title
            "image": f"https://source.unsplash.com/featured/?crypto,finance,{blog_data['category']}",
            "_archived": False,
            "_draft": True 
        }
    }
    
    print(f"Sending to Webflow: {blog_data['title']}...")
    res = requests.post(url, json=payload, headers=headers)
    
    if res.status_code in [200, 201, 202]:
        print(f"Success! {blog_data['category']} post is in Webflow.")
    else:
        print(f"Error from Webflow: {res.text}")

if __name__ == "__main__":
    try:
        blog_content = generate_blog_content()
        post_to_webflow(blog_content)
    except Exception as e:
        print(f"An error occurred: {e}")
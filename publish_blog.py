import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
WEBFLOW_TOKEN = os.getenv("WEBFLOW_API_TOKEN")
COLLECTION_ID = os.getenv("WEBFLOW_COLLECTION_ID")

PUBLISHED_LOG = "published_articles.json"  # čuva koji indexi su već objavljeni

# ... (BRAND_CONTEXT, SYSTEM_PROMPT, CONTENT_POOL ostaju isti)

def load_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, "r") as f:
            return json.load(f)
    return []

def save_published(published_list):
    with open(PUBLISHED_LOG, "w") as f:
        json.dump(published_list, f, indent=2)

def pick_article():
    published = load_published()
    
    # Ako su svi objavljeni, resetuj log (počni iznova)
    if len(published) >= len(CONTENT_POOL):
        print("Svi artikli su objavljeni, resetujem log...")
        published = []
        save_published(published)
    
    # Nađi prvi neobjavljeni index
    for idx in range(len(CONTENT_POOL)):
        if idx not in published:
            return idx, CONTENT_POOL[idx]
    
    raise Exception("Nije pronađen neobjavljeni artikal")

def build_prompt(article):
    year = datetime.utcnow().year
    month = datetime.utcnow().strftime("%B")
    title = article["title_template"].replace("[YEAR]", str(year)).replace("[MONTH]", month)

    format_instructions = {
        # ... isti kao pre, ali DODAJ heading uputstvo svuda
    }

    structure = format_instructions.get(article["format"], "Use clear headings with detailed paragraphs under each.")

    # NOVO: heading hierarchy pravilo
    heading_rules = (
        "\n\nHEADING HIERARCHY RULES (strictly follow):\n"
        "- Use MAXIMUM 4-5 H2 tags in the entire article. H2 is reserved for major sections only.\n"
        "- Use H3 for subsections within an H2 section.\n"
        "- Use H4 only when nesting is truly needed (rare).\n"
        "- Example structure: H2 > H3 > H3 > H2 > H3 > H3. Never 10+ H2s in a row.\n"
        "- The Table of Contents should only reflect H2 headings, so keep them broad and meaningful.\n"
    )

    prompt = (
        BRAND_CONTEXT + "\n\n"
        "Write a blog post for Piggy (piggysave.app).\n\n"
        "TITLE: " + title + "\n"
        "CATEGORY: " + article["category"] + "\n"
        "FORMAT: " + article["format"] + "\n"
        "TARGET KEYWORD: " + article["keyword"] + "\n"
        "WORD COUNT TARGET: " + article["word_count"] + " words\n"
        "ANGLE: " + article["angle"] + "\n\n"
        "STRUCTURE TO FOLLOW:\n" + structure + "\n"
        + heading_rules +
        "\nStart with a hook: a surprising stat, a relatable scenario, or a provocative statement.\n"
        "Do not write a boring 'In today's article...' intro.\n\n"
        "Return ONLY a valid JSON object with no markdown and no code fences:\n"
        '{"title": "' + title + '", "summary": "1-2 sentence meta description", "html_content": "<h2>...</h2><p>...</p>", "category": "' + article["category"] + '"}'
    )
    return prompt


def generate_blog_content():
    import time
    article_idx, article = pick_article()  # <- sada vraća i index
    print("Generating: [" + article["category"] + "] " + article["title_template"][:60] + "...")

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key=" + GEMINI_KEY

    max_retries = 4
    wait_seconds = 30

    for attempt in range(1, max_retries + 1):
        response = requests.post(
            url,
            json={
                "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": [{"parts": [{"text": build_prompt(article)}]}],
                "generationConfig": {"temperature": 0.8, "maxOutputTokens": 8192}
            }
        )

        if response.status_code == 200:
            raw_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            clean = raw_text.replace("```json", "").replace("```", "").strip()
            result = json.loads(clean)
            result["_article_idx"] = article_idx  # prosleđujemo index dalje
            return result
        elif response.status_code in [503, 429]:
            if attempt < max_retries:
                print("Gemini busy (attempt " + str(attempt) + "), retrying in " + str(wait_seconds) + "s...")
                time.sleep(wait_seconds)
            else:
                raise Exception("Gemini Error after " + str(max_retries) + " attempts: " + str(response.status_code) + " - " + response.text)
        else:
            raise Exception("Gemini Error: " + str(response.status_code) + " - " + response.text)


def post_to_webflow(data):
    url = "https://api.webflow.com/v2/collections/" + COLLECTION_ID + "/items/live"

    headers = {
        "Authorization": "Bearer " + WEBFLOW_TOKEN,
        "accept-version": "2.0.0",
        "content-type": "application/json"
    }

    payload = {
        "isArchived": False,
        "isDraft": False,
        "fieldData": {
            "name": data["title"],
            "post-body": data["html_content"],
            "post-summary": data["summary"],
            "category": data["category"],
            "featured": False
        }
    }

    print("Publishing to Webflow: " + data["title"] + "...")
    res = requests.post(url, json=payload, headers=headers)

    if res.status_code in [200, 201, 202]:
        # NOVO: tek nakon uspešnog posta, snimi index kao objavljen
        published = load_published()
        published.append(data["_article_idx"])
        save_published(published)
        print("Success! " + data["title"] + " is now LIVE.")
    else:
        raise Exception("Webflow Error: " + str(res.status_code) + " - " + res.text)


if __name__ == "__main__":
    try:
        content = generate_blog_content()
        post_to_webflow(content)
    except Exception as e:
        print("Failed: " + str(e))
        raise

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
WEBFLOW_TOKEN = os.getenv("WEBFLOW_API_TOKEN")
COLLECTION_ID = os.getenv("WEBFLOW_COLLECTION_ID")

PUBLISHED_LOG = "published_articles.json"

BRAND_CONTEXT = (
    "Piggy (piggysave.app) is a personal finance brand - think mini-NerdWallet but written like a smart friend texting you advice. "
    "The blog is a personal finance destination that stands on its own before the app launches. "
    "Tone: Warm, opinionated, accessible. No jargon without explanation. 8th-grade reading level. Recommend specific products/actions - no 'it depends' hedging. "
    "Positioning: The finance site that does not make you feel dumb. "
    "Do NOT mention Web3, Farcaster, Zora, or the old Propaganda/Piggybank product. "
    "Always end articles with: <p><em>This is educational content, not financial advice.</em></p>"
)

SYSTEM_PROMPT = (
    "You are a world-class personal finance writer for Piggy (piggysave.app). "
    "Your style: warm, direct, opinionated, accessible. Like a knowledgeable friend, not a textbook. "
    "You write at an 8th-grade reading level. You recommend specific products and give real answers. "
    "You never say 'it depends on your situation' without following it with an actual decision framework. "
    "Never use passive voice where active works. Never pad content with filler sentences."
)

CATEGORIES = [
    "Save",
    "Invest",
    "Spend Smart",
    "Tools & Reviews",
    "Money 101",
    "Taxes",
    "Earn",
]


def load_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, "r") as f:
            return json.load(f)
    return []


def save_published(published_list):
    with open(PUBLISHED_LOG, "w") as f:
        json.dump(published_list, f, indent=2)


def pick_category(published_titles):
    # Rotate through categories evenly based on how many times each has been used
    # Count how many published titles belong to each category (we store category too)
    # Since we only stored titles before, just rotate by count
    counts = {cat: 0 for cat in CATEGORIES}
    for entry in published_titles:
        if isinstance(entry, dict) and "category" in entry:
            cat = entry["category"]
            if cat in counts:
                counts[cat] += 1
    # Pick the category with fewest posts
    return min(counts, key=counts.get)


def generate_topic_and_content(published_titles):
    import time

    year = datetime.utcnow().year
    month = datetime.utcnow().strftime("%B")

    category = pick_category(published_titles)

    # Build list of already published titles to avoid repetition
    already_published = []
    for entry in published_titles:
        if isinstance(entry, dict):
            already_published.append(entry["title"])
        elif isinstance(entry, str):
            already_published.append(entry)

    already_published_str = "\n".join(f"- {t}" for t in already_published) if already_published else "None yet."

    topic_prompt = (
        BRAND_CONTEXT + "\n\n"
        f"Current year: {year}. Current month: {month}.\n\n"
        f"You are generating a NEW blog post for the category: {category}\n\n"
        "ALREADY PUBLISHED TITLES (do NOT repeat or closely resemble these):\n"
        + already_published_str + "\n\n"
        "Your job:\n"
        "1. Pick a fresh, specific personal finance topic for this category that is NOT similar to any already published title.\n"
        "2. Write a full blog post for it.\n\n"
        "WRITING RULES:\n"
        "- Start with a hook: a surprising stat, a relatable scenario, or a provocative statement.\n"
        "- Do not write a boring 'In today's article...' intro.\n"
        "- Word count: 1500-2500 words.\n"
        "- Use H2 for major sections (max 5 H2s total), H3 for subsections.\n"
        "- Recommend specific products, apps, accounts by name.\n"
        "- End with: <p><em>This is educational content, not financial advice.</em></p>\n\n"
        "Return ONLY a valid JSON object with no markdown and no code fences:\n"
        '{"title": "Your chosen title", "summary": "1-2 sentence meta description", '
        '"html_content": "<h2>...</h2><p>...</p>", "category": "' + category + '"}'
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_KEY}"

    max_retries = 4
    wait_seconds = 30

    for attempt in range(1, max_retries + 1):
        response = requests.post(
            url,
            json={
                "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": [{"parts": [{"text": topic_prompt}]}],
                "generationConfig": {"temperature": 0.9, "maxOutputTokens": 8192}
            }
        )

        if response.status_code == 200:
            raw_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            clean = raw_text.replace("```json", "").replace("```", "").strip()
            result = json.loads(clean)
            return result
        elif response.status_code in [503, 429]:
            if attempt < max_retries:
                print(f"Gemini busy (attempt {attempt}), retrying in {wait_seconds}s...")
                time.sleep(wait_seconds)
            else:
                raise Exception(f"Gemini Error after {max_retries} attempts: {response.status_code} - {response.text}")
        else:
            raise Exception(f"Gemini Error: {response.status_code} - {response.text}")


def post_to_webflow(data, published_list):
    url = f"https://api.webflow.com/v2/collections/{COLLECTION_ID}/items/live"

    headers = {
        "Authorization": f"Bearer {WEBFLOW_TOKEN}",
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

    print(f"Publishing to Webflow: {data['title']}...")
    res = requests.post(url, json=payload, headers=headers)

    if res.status_code in [200, 201, 202]:
        published_list.append({
            "title": data["title"],
            "category": data["category"],
            "date": datetime.utcnow().strftime("%Y-%m-%d")
        })
        save_published(published_list)
        print(f"Success! {data['title']} is now LIVE.")
    else:
        raise Exception(f"Webflow Error: {res.status_code} - {res.text}")


if __name__ == "__main__":
    try:
        published = load_published()
        print(f"DEBUG - Ukupno objavljenih: {len(published)}")

        content = generate_topic_and_content(published)
        print(f"DEBUG - Generisan naslov: {content['title']}")

        post_to_webflow(content, published)
    except Exception as e:
        print(f"Failed: {str(e)}")
        raise

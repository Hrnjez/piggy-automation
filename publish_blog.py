import os
import re
import time
import json
import requests
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

SIMILARITY_THRESHOLD = 0.5
MAX_GEN_ATTEMPTS = 5

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "your", "you", "how", "why", "what", "is", "are", "was",
    "be", "by", "from", "that", "this", "it", "as", "if", "my", "our",
    "their", "its", "we", "i", "not", "no", "do", "did", "has", "have",
    "will", "can", "should", "without", "never", "ever", "more", "most",
    "than", "into", "up", "out", "about", "just", "get", "make", "take",
    "2026", "2025", "vs", "heres", "actually", "really", "only", "every",
}


# ─── Published log ────────────────────────────────────────────────────────────

def load_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, "r") as f:
            return json.load(f)
    return []


def save_published(published_list):
    with open(PUBLISHED_LOG, "w") as f:
        json.dump(published_list, f, indent=2)


# ─── Similarity check ─────────────────────────────────────────────────────────

def is_too_similar(new_title, published_list, threshold=SIMILARITY_THRESHOLD):
    new_words = set(new_title.lower().split()) - STOPWORDS
    if not new_words:
        return False, None

    for entry in published_list:
        existing = entry["title"] if isinstance(entry, dict) else entry
        existing_words = set(existing.lower().split()) - STOPWORDS
        if not existing_words:
            continue
        overlap = len(new_words & existing_words) / max(len(new_words), 1)
        if overlap > threshold:
            return True, existing

    return False, None


# ─── Category picker ──────────────────────────────────────────────────────────

def pick_category(published_list):
    counts = {cat: 0 for cat in CATEGORIES}
    for entry in published_list:
        if isinstance(entry, dict) and "category" in entry:
            cat = entry["category"]
            if cat in counts:
                counts[cat] += 1
    return min(counts, key=counts.get)


# ─── Content generation ───────────────────────────────────────────────────────

def generate_topic_and_content(published_list):
    year = datetime.utcnow().year
    month = datetime.utcnow().strftime("%B")
    category = pick_category(published_list)

    recent_entries = published_list[-80:]
    recent_titles = [
        e["title"] if isinstance(e, dict) else e
        for e in recent_entries
    ]
    already_published_str = "\n".join(f"- {t}" for t in recent_titles) or "None yet."

    topic_prompt = (
        BRAND_CONTEXT + "\n\n"
        f"Current year: {year}. Current month: {month}.\n\n"
        f"You are generating a NEW blog post for the category: {category}\n\n"
        "RECENTLY PUBLISHED TITLES (avoid similar topics AND similar concepts, not just similar wording):\n"
        + already_published_str + "\n\n"
        "Your job:\n"
        "1. Pick a fresh, specific personal finance topic for this category.\n"
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
            resp_json = response.json()
            candidates = resp_json.get("candidates", [])

            if not candidates:
                print(f"Attempt {attempt}: No candidates in response: {resp_json}")
                if attempt < max_retries:
                    time.sleep(wait_seconds)
                    continue
                raise Exception(f"No candidates after {max_retries} attempts. Last response: {resp_json}")

            raw_text = candidates[0]["content"]["parts"][0]["text"]
            clean = raw_text.replace("```json", "").replace("```", "").strip()

            json_match = re.search(r'\{.*\}', clean, re.DOTALL)
            if not json_match:
                print(f"Attempt {attempt}: No JSON found. Raw: {clean[:300]}")
                if attempt < max_retries:
                    time.sleep(wait_seconds)
                    continue
                raise Exception("No valid JSON found in response after all retries.")

            try:
                result = json.loads(json_match.group())
                return result
            except json.JSONDecodeError as e:
                print(f"Attempt {attempt}: JSON parse error: {e}. Raw: {clean[:300]}")
                if attempt < max_retries:
                    time.sleep(wait_seconds)
                    continue
                raise

        elif response.status_code in [429, 503]:
            if attempt < max_retries:
                print(f"Gemini busy (attempt {attempt}), retrying in {wait_seconds}s...")
                time.sleep(wait_seconds)
            else:
                raise Exception(
                    f"Gemini Error after {max_retries} attempts: {response.status_code} - {response.text}"
                )
        else:
            raise Exception(f"Gemini Error: {response.status_code} - {response.text}")


# ─── Webflow publish ───────────────────────────────────────────────────────────

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
        print(f"Success! '{data['title']}' is now LIVE.")
    else:
        raise Exception(f"Webflow Error: {res.status_code} - {res.text}")


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        published = load_published()
        print(f"DEBUG - Ukupno objavljenih: {len(published)}")

        content = None
        last_candidate = None

        for gen_attempt in range(1, MAX_GEN_ATTEMPTS + 1):
            print(f"Generacija pokusaj {gen_attempt}/{MAX_GEN_ATTEMPTS}...")
            candidate = generate_topic_and_content(published)
            last_candidate = candidate

            too_similar, similar_to = is_too_similar(candidate["title"], published)

            if not too_similar:
                content = candidate
                print(f"✓ Unikatan naslov pronadjen: {candidate['title']}")
                break
            else:
                print(f"✗ Previše slično sa '{similar_to}', regenerišem...")

        if content is None:
            print(f"WARNING: Nije pronadjen unikatan naslov nakon {MAX_GEN_ATTEMPTS} pokusaja.")
            print(f"Objavljujem poslednji kandidat: {last_candidate['title']}")
            content = last_candidate

        print(f"DEBUG - Generisan naslov: {content['title']}")
        post_to_webflow(content, published)

    except Exception as e:
        print(f"Failed: {str(e)}")
        raise
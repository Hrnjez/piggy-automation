import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load keys
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

CONTENT_POOL = [
    {
        "category": "Save",
        "title_template": "How to Save $10,000 in a Year: The Plan That Actually Works",
        "keyword": "how to save $10000 in a year",
        "format": "Complete Guide",
        "word_count": "2500-3500",
        "angle": "Step-by-step guide with income tiers ($30k, $50k, $75k+). Include automation strategies, specific savings accounts, and a month-by-month breakdown."
    },
    {
        "category": "Save",
        "title_template": "The 52-Week Savings Challenge: Complete Guide for [YEAR]",
        "keyword": "52 week savings challenge",
        "format": "Challenge Guide",
        "word_count": "1500-2000",
        "angle": "Full challenge explanation with a printable-style week-by-week table in HTML, variations for different income levels, and best accounts to park the money."
    },
    {
        "category": "Save",
        "title_template": "How Much Should You Have Saved by 30? (Real Numbers, Not Fantasy)",
        "keyword": "how much should you have saved by 30",
        "format": "How Much",
        "word_count": "1500-2000",
        "angle": "Data-driven benchmarks, why most advice is unrealistic, what to do if you're behind, and specific steps to catch up."
    },
    {
        "category": "Save",
        "title_template": "Stop Budgeting. Automate Your Money Instead. (Here's How)",
        "keyword": "automate savings",
        "format": "Anti-Advice",
        "word_count": "1200-1800",
        "angle": "Contrarian take that budgets fail because willpower is finite. Automation blueprint: split accounts, auto-transfers, specific apps (Ally, Marcus, Fidelity)."
    },
    {
        "category": "Invest",
        "title_template": "Should You Invest in Bitcoin in [YEAR]? Here's What to Know",
        "keyword": "should I invest in bitcoin",
        "format": "Should You Invest",
        "word_count": "1800-2500",
        "angle": "Honest risk/reward breakdown. Historical performance, how much to allocate (% of portfolio), best platforms (Coinbase, Robinhood). Not hype, not FUD."
    },
    {
        "category": "Invest",
        "title_template": "How to Start Investing in Stocks: A Beginner's Guide for [YEAR]",
        "keyword": "how to start investing in stocks",
        "format": "Complete Guide",
        "word_count": "2500-3500",
        "angle": "True beginner guide: brokerage accounts, index funds vs individual stocks, how much to start with, specific platform picks (Robinhood, Fidelity, Schwab)."
    },
    {
        "category": "Invest",
        "title_template": "How to Build Wealth in Your 20s: The Playbook No One Gave You",
        "keyword": "build wealth in your 20s",
        "format": "Complete Guide",
        "word_count": "2500-3500",
        "angle": "Priority order: emergency fund, 401k match, HYSA, Roth IRA, brokerage. Specific action items for each income level."
    },
    {
        "category": "Spend Smart",
        "title_template": "The 30% Rent Rule: Does It Still Work in [YEAR]? (Honest Answer: Barely)",
        "keyword": "30 percent rent rule",
        "format": "Financial Rules",
        "word_count": "1500-2000",
        "angle": "History of the rule, why it breaks down in major cities, what alternatives exist (25% take-home rule), with real city examples."
    },
    {
        "category": "Spend Smart",
        "title_template": "The 50/30/20 Rule Explained: A Budget Framework That Actually Works",
        "keyword": "50 30 20 rule",
        "format": "Financial Rules",
        "word_count": "1500-2000",
        "angle": "What it is, how to apply it, why it works better than line-item budgets, variations for low/high incomes."
    },
    {
        "category": "Spend Smart",
        "title_template": "The Subscription Audit: How to Find and Cancel the $273/Month You Forgot About",
        "keyword": "subscription audit",
        "format": "True Cost",
        "word_count": "1000-1500",
        "angle": "Step-by-step audit process, specific apps to find subscriptions (Rocket Money, Trim), decision framework for what to keep/cut."
    },
    {
        "category": "Tools & Reviews",
        "title_template": "Best High-Yield Savings Accounts: [MONTH] [YEAR] (Rates Updated)",
        "keyword": "best high yield savings accounts",
        "format": "Best Products",
        "word_count": "1500-2000",
        "angle": "Current top picks (Marcus, Ally, SoFi, UFB Direct) with rates, minimums, and who each is best for. Updated monthly framing."
    },
    {
        "category": "Tools & Reviews",
        "title_template": "Best Stock Trading Apps for Beginners in [YEAR] (We'd Pick Robinhood)",
        "keyword": "best stock trading apps for beginners",
        "format": "Best Products",
        "word_count": "1500-2000",
        "angle": "Top 5 apps compared (Robinhood, Fidelity, Schwab, Webull, SoFi Invest) with a clear recommendation and who each suits best."
    },
    {
        "category": "Money 101",
        "title_template": "What Is Compound Interest? (The Explainer That Actually Makes Sense)",
        "keyword": "what is compound interest",
        "format": "What Is",
        "word_count": "1000-1500",
        "angle": "Simple analogy-first explanation, real math examples with small starting amounts, why starting early matters more than investing more later."
    },
    {
        "category": "Money 101",
        "title_template": "Roth IRA vs. Traditional IRA: The 5-Minute Guide to Picking the Right One",
        "keyword": "roth ira vs traditional ira",
        "format": "A vs B",
        "word_count": "1500-2000",
        "angle": "Clear comparison table, simple decision rule (pay taxes now vs later), income limits, contribution limits for current year."
    },
    {
        "category": "Money 101",
        "title_template": "Saving vs. Investing: When to Do Which (The Decision Framework)",
        "keyword": "saving vs investing",
        "format": "A vs B",
        "word_count": "1200-1800",
        "angle": "Clear framework: save for goals under 5 years, invest for goals over 5 years. Emergency fund first. Specific product picks for each path."
    },
    {
        "category": "Taxes",
        "title_template": "Trump Accounts Explained: The New $1,000 Savings Account for Kids (2026 Guide)",
        "keyword": "trump accounts",
        "format": "Complete Guide",
        "word_count": "2000-2500",
        "angle": "What Trump Accounts are, how they work, eligibility, contribution limits, how they compare to 529s and Roth IRAs, step-by-step to open one."
    },
    {
        "category": "Taxes",
        "title_template": "What to Do With Your Tax Refund in 2026 (5 Moves That Actually Build Wealth)",
        "keyword": "what to do with tax refund",
        "format": "What to Do With",
        "word_count": "1200-1800",
        "angle": "Ranked priority list: emergency fund, high-interest debt, IRA contribution, HYSA, invest. Opinionated, specific."
    },
    {
        "category": "Earn",
        "title_template": "5 Realistic Side Hustles That Actually Pay in [YEAR]",
        "keyword": "realistic side hustles",
        "format": "Listicle",
        "word_count": "1500-2000",
        "angle": "5 vetted options with real income ranges, time required, startup cost, and who each is best for. No MLM, no dropshipping fantasy."
    },
]


def load_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, "r") as f:
            data = json.load(f)
            return [int(x) for x in data]  # fix: osiguraj da su brojevi, ne stringovi
    return []


def save_published(published_list):
    with open(PUBLISHED_LOG, "w") as f:
        json.dump(published_list, f, indent=2)


def pick_article():
      published = load_published()
        print(f"DEBUG - Objavljeni indeksi: {published}")
        print(f"DEBUG - Ukupno artikala u poolu: {len(CONTENT_POOL)}")

    if len(published) >= len(CONTENT_POOL):
        print("Svi artikli objavljeni, resetujem log...")
        published = []
        save_published(published)

    for idx in range(len(CONTENT_POOL)):
        if idx not in published:
            return idx, CONTENT_POOL[idx]

    raise Exception("Nije pronađen neobjavljeni artikal")


def build_prompt(article):
    year = datetime.utcnow().year
    month = datetime.utcnow().strftime("%B")
    title = article["title_template"].replace("[YEAR]", str(year)).replace("[MONTH]", month)

    format_instructions = {
        "Complete Guide": "Structure: H2 What Is [Topic], then H3 subsections, H2 Step-by-Step Guide with H3 steps, H2 Common Mistakes with H3s, H2 Best Tools and Apps, H2 FAQ, H2 The Bottom Line.",
        "Should You Invest": "Structure: H2 What Is [Asset], H2 Historical Performance with H3s, H2 Pros and Risks as H3s, H2 How to Buy It, H2 How Much to Invest, H2 Who This Is For, H2 FAQ.",
        "Best Products": "Structure: Opening on evaluation criteria, H2 for each product with H3 pros/cons/our take, H2 How to Choose, H2 FAQ.",
        "Financial Rules": "Structure: H2 What the Rule Says, H2 Does It Still Work with H3s, H2 When to Break the Rule, H2 A Better Framework, H2 FAQ.",
        "A vs B": "Structure: H2 Quick Summary, H2 Key Differences with H3s and HTML table, H2 When to Choose A with H3s, H2 When to Choose B with H3s, H2 The Bottom Line.",
        "Challenge Guide": "Structure: H2 How It Works, H2 The Full Week-by-Week Table in HTML, H2 Variations for Different Incomes with H3s, H2 Best Accounts to Use, H2 FAQ.",
        "How Much": "Structure: H2 The Benchmarks, H2 Why Most Advice Is Wrong, H2 What to Do If You're Behind with H3 steps, H2 The Bottom Line.",
        "Anti-Advice": "Structure: H2 Why [Common Advice] Fails, H2 The Automation Blueprint with H3 steps, H2 Specific Tools and Apps, H2 FAQ.",
        "True Cost": "Structure: H2 How to Do the Audit with H3 steps, H2 Tools That Help, H2 What to Keep vs Cut framework, H2 The Bottom Line.",
        "What Is": "Structure: H2 The Simple Explanation, H2 Real Math Examples with H3s, H2 Why It Matters for You, H2 How to Take Advantage, H2 FAQ.",
        "What to Do With": "Structure: H2 Priority Order with H3 for each move, H2 What NOT to Do, H2 FAQ.",
        "Listicle": "Structure: H2 for each item with H3 subsections (income range, time required, startup cost, best for), H2 How to Pick the Right One, H2 FAQ.",
    }

    structure = format_instructions.get(article["format"], "Use clear H2/H3 headings with detailed paragraphs under each.")

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
    article_idx, article = pick_article()
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
            result["_article_idx"] = article_idx
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

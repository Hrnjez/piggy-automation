import os
import requests
import json
import random
from datetime import datetime
from dotenv import load_dotenv

# Load keys
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
WEBFLOW_TOKEN = os.getenv("WEBFLOW_API_TOKEN")
COLLECTION_ID = os.getenv("WEBFLOW_COLLECTION_ID")

# ─────────────────────────────────────────────
# CONTENT STRATEGY CONFIG
# Based on Piggy Blog Content Strategy v2
# ─────────────────────────────────────────────

BRAND_CONTEXT = """
Piggy (piggysave.app) is a personal finance brand — think mini-NerdWallet but written like a smart friend texting you advice.
The blog is a personal finance destination that stands on its own before the app launches.
Tone: Warm, opinionated, accessible. No jargon without explanation. 8th-grade reading level. Recommend specific products/actions — no "it depends" hedging.
Positioning: "The finance site that doesn't make you feel dumb."
Do NOT mention Web3, Farcaster, Zora, or the old Propaganda/Piggybank product.
Always end articles with: <p><em>This is educational content, not financial advice.</em></p>
"""

# Format templates mapped by category
CONTENT_POOL = [
    # SAVE
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
    # INVEST
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
        "angle": "Priority order: emergency fund → 401k match → HYSA → Roth IRA → brokerage. Specific action items for each income level."
    },
    # SPEND SMART
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
    # TOOLS & REVIEWS
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
    # MONEY 101
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
        "angle": "Clear framework: save for goals <5 years, invest for goals >5 years. Emergency fund first. Specific product picks for each path."
    },
    # TAXES (Trending)
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
        "angle": "Ranked priority list: emergency fund → high-interest debt → IRA contribution → HYSA → invest. Opinionated, specific."
    },
    # EARN
    {
        "category": "Earn",
        "title_template": "5 Realistic Side Hustles That Actually Pay in [YEAR]",
        "keyword": "realistic side hustles",
        "format": "Listicle",
        "word_count": "1500-2000",
        "angle": "5 vetted options with real income ranges, time required, startup cost, and who each is best for. No MLM, no dropshipping fantasy."
    },
]

SYSTEM_PROMPT = """You are a world-class personal finance writer for Piggy (piggysave.app).
Your style: warm, direct, opinionated, accessible. Like a knowledgeable friend, not a textbook.
You write at an 8th-grade reading level. You recommend specific products and give real answers.
You never say "it depends on your situation" without following it with an actual decision framework.
Never use passive voice where active works. Never pad content with filler sentences."""


def pick_article():
    """Pick an article from the content pool, rotating by hour of day."""
    hour = datetime.utcnow().hour
    idx = (datetime.utcnow().timetuple().tm_yday + hour) % len(CONTENT_POOL)
    return CONTENT_POOL[idx]


def build_prompt(article: dict) -> str:
    year = datetime.utcnow().year
    month = datetime.utcnow().strftime("%B")
    title = article["title_template"].replace("[YEAR]", str(year)).replace("[MONTH]", month)

    format_instructions = {
        "Complete Guide": """
Structure:
- H2: What Is [Topic]? (plain English, 1-2 paragraphs)
- H2: Why It Matters Right Now
- H2: Step-by-Step Guide (H3 for each step)
- H2: Common Mistakes (3-5, each with a fix)
- H2: Best Tools and Apps (specific recommendations with honest pros/cons)
- H2: FAQ (5-6 questions)
- H2: The Bottom Line (1 paragraph + one concrete action)""",
        "Should You Invest": """
Structure:
- H2: What Is [Asset]? (quick explainer)
- H2: Historical Performance (honest, with context)
- H2: Pros of Investing
- H2: Risks and Downsides (be honest)
- H2: How to Actually Buy It (step-by-step)
- H2: How Much Should You Invest? (% allocation by risk profile)
- H2: [Asset] vs. Alternatives (comparison)
- H2: Who This Is (and Isn't) For
- H2: FAQ""",
        "Best Products": """
Structure:
- Opening: What we looked for and how we evaluated
- H2 for each product: Name, rating, best for, pros, cons, our take
- H2: How to Choose (decision matrix)
- H2: FAQ""",
        "Financial Rules": """
Structure:
- H2: What the Rule Says
- H2: Where It Came From
- H2: Does It Still Work? (honest assessment with data)
- H2: When to Break the Rule
- H2: A Better Framework
- H2: FAQ""",
        "A vs B": """
Structure:
- H2: Quick Summary (decision table)
- H2: What Is [A]?
- H2: What Is [B]?
- H2: Key Differences (comparison table in HTML)
- H2: When to Choose [A]
- H2: When to Choose [B]
- H2: The Bottom Line (clear recommendation)""",
    }

    structure = format_instructions.get(article["format"], "Use clear H2/H3 headings with detailed paragraphs under each.")

    return f"""
{BRAND_CONTEXT}

Write a blog post for Piggy (piggysave.app).

TITLE: {title}
CATEGORY: {article['category']}
FORMAT: {article['format']}
TARGET KEYWORD: {article['keyword']}
WORD COUNT TARGET: {article['word_count']} words
ANGLE: {article['angle']}

STRUCTURE TO FOLLOW:
{structure}

Start with a hook: a surprising stat, a relatable scenario, or a provocative statement. 
Do not write a boring "In today's article..." intro.

Return ONLY a valid JSON object (no markdown, no code fences):
{{
  "title": "{title}",
  "summary": "1-2 sentence meta description optimized for the keyword",
  "html_content": "<h2>...</h2><p>...</p>... (full article HTML)",
  "category": "{article['category']}"
}}
"""


def generate_blog_content():
    article = pick_article()
    print(f"Generating: [{article['category']}] {article['title_template'][:60]}...")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"

    response = requests.post(
        url,
        json={
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"parts": [{"text": build_prompt(article)}]}],
            "generationConfig": {"temperature": 0.8, "maxOutputTokens": 8192}
        }
    )

    if response.status_code == 200:
        raw_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        # Strip any accidental markdown fences
        clean = raw_text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean)
    else:
        raise Exception(f"Gemini Error: {response.status_code} — {response.text}")


def post_to_webflow(data):
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
            "name": data['title'],
            "post-body": data['html_content'],
            "post-summary": data['summary'],
            "category": data['category'],
            "featured": False
        }
    }

    print(f"Publishing to Webflow: '{data['title']}'...")
    res = requests.post(url, json=payload, headers=headers)

    if res.status_code in [200, 201, 202]:
        print(f"✅ Success! '{data['title']}' is now LIVE.")
    else:
        raise Exception(f"Webflow Error: {res.status_code} — {res.text}")


if __name__ == "__main__":
    try:
        content = generate_blog_content()
        post_to_webflow(content)
    except Exception as e:
        print(f"❌ Failed: {e}")
        raise

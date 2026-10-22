
import urllib.request
import xml.etree.ElementTree as ET
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote

RSS_URL = "https://feeds.bbci.co.uk/news/world/rss.xml"

IMPORTANT_KEYWORDS = [
    "breaking", "major", "government", "election", "court",
    "policy", "economy", "crisis", "war", "attack", "disaster",
    "earthquake", "flood", "storm", "health", "disease",
    "research", "discovery", "technology", "security",
    "climate", "business", "science", "india", "urgent"
]

CLICKBAIT_WORDS = [
    "you won't believe", "shocking", "mind-blowing",
    "must see", "unbelievable", "secret trick"
]


def clean_text(text):
    """Remove HTML tags and extra whitespace."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", text).strip()


def get_score(title, description):
    """Give higher scores to potentially important stories."""
    text = f"{title} {description}".lower()
    score = 0

    for keyword in IMPORTANT_KEYWORDS:
        if keyword in text:
            score += 2

    for phrase in CLICKBAIT_WORDS:
        if phrase in title.lower():
            score -= 5

    if len(title.split()) < 4:
        score -= 2

    return score


def fetch_news(category=None, query=None, limit=20):
    """Fetch, filter, deduplicate, and rank news articles."""
    request = urllib.request.Request(
        RSS_URL,
        headers={"User-Agent": "DailyScope/1.0"}
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            root = ET.fromstring(response.read())
    except Exception as error:
        print(f"News fetch failed: {error}")
        return []

    articles = []
    seen_titles = set()

    for item in root.findall(".//item"):
        title = clean_text(item.findtext("title", ""))
        description = clean_text(item.findtext("description", ""))
        link = item.findtext("link", "").strip()
        pub_date = item.findtext("pubDate", "").strip()

        if not title or not link:
            continue

        # Remove duplicate headlines.
        normalized = re.sub(r"[^a-z0-9]", "", title.lower())
        if normalized in seen_titles:
            continue
        seen_titles.add(normalized)

        # Filter clickbait headlines.
        if any(word in title.lower() for word in CLICKBAIT_WORDS):
            continue

        # Optional keyword search.
        if query:
            searchable = f"{title} {description}".lower()
            if query.lower() not in searchable:
                continue

        # Assign a category using simple keyword matching.
        text = f"{title} {description}".lower()

        categories = {
            "India": ["india", "indian", "delhi", "mumbai"],
            "Technology": ["technology", "tech", "artificial intelligence", " AI "],
            "Science": ["science", "research", "scientist", "discovery"],
            "Business": ["business", "economy", "market", "company", "trade"],
            "World": ["world", "international", "global", "government"]
        }

        article_category = "World"

        for name, keywords in categories.items():
            if any(word in text for word in keywords):
                article_category = name
                break

        if category and category.lower() != article_category.lower():
            continue

        # Parse publication date.
        published = ""
        try:
            published = parsedate_to_datetime(pub_date).strftime(
                "%d %b %Y, %H:%M"
            )
        except (ValueError, TypeError, OverflowError):
            published = pub_date

        articles.append({
            "title": title,
            "description": description,
            "link": link,
            "published": published,
            "category": article_category,
            "score": get_score(title, description)
        })

    # Show higher-priority stories first.
    articles.sort(key=lambda article: article["score"], reverse=True)

    return articles[:max(0, limit)]

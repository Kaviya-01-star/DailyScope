import re
import html
import urllib.request
import xml.etree.ElementTree as ET

from email.utils import parsedate_to_datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


RSS_FEEDS = {
    "India": [
        ("Google News", "https://news.google.com/rss/search?q=India+news&hl=en-IN&gl=IN&ceid=IN:en"),
        ("BBC", "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml"),
    ],
    "World": [
        ("BBC", "https://feeds.bbci.co.uk/news/world/rss.xml"),
        ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
        ("Google News", "https://news.google.com/rss/search?q=world+news&hl=en-IN&gl=IN&ceid=IN:en"),
    ],
    "Business": [
        ("BBC", "https://feeds.bbci.co.uk/news/business/rss.xml"),
        ("Google News", "https://news.google.com/rss/search?q=business+news&hl=en-IN&gl=IN&ceid=IN:en"),
    ],
    "Science": [
        ("BBC", "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml"),
        ("Google News", "https://news.google.com/rss/search?q=science+news&hl=en-IN&gl=IN&ceid=IN:en"),
    ],
    "Technology": [
        ("BBC", "https://feeds.bbci.co.uk/news/technology/rss.xml"),
        ("Google News", "https://news.google.com/rss/search?q=technology+news&hl=en-IN&gl=IN&ceid=IN:en"),
    ],
    "Sports": [
        ("BBC", "https://feeds.bbci.co.uk/sport/rss.xml"),
        ("ESPN", "https://www.espn.com/espn/rss/news"),
        ("Google News", "https://news.google.com/rss/search?q=sports+news&hl=en-IN&gl=IN&ceid=IN:en"),
    ],
}


def clean_text(value):
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def make_summary(description, title):
    """Free excerpt-based summary; no paid AI service."""
    text = clean_text(description)

    if not text or text.lower() == title.lower():
        return "Read the original article for the complete story."

    if len(text) <= 280:
        return text

    shortened = text[:280]
    last_space = shortened.rfind(" ")

    if last_space > 180:
        shortened = shortened[:last_space]

    return shortened.rstrip(" .,;:") + "..."


def fetch_feed(source, url, category):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "DailyScope/1.0"}
    )

    with urllib.request.urlopen(request, timeout=12) as response:
        root = ET.fromstring(response.read())

    articles = []

    for item in root.findall(".//item"):
        title = clean_text(item.findtext("title", ""))
        description = clean_text(
            item.findtext("description", "")
        )
        link = item.findtext("link", "").strip()
        pub_date = item.findtext("pubDate", "").strip()

        if not title or not link:
            continue

        published = ""
        timestamp = 0

        try:
            date = parsedate_to_datetime(pub_date)
            timestamp = date.timestamp()
            published = date.strftime("%d %b %Y, %H:%M UTC")
        except (ValueError, TypeError, OverflowError):
            pass

        articles.append({
            "title": title,
            "description": description,
            "summary": make_summary(description, title),
            "link": link,
            "published": published,
            "category": category,
            "source": source,
            "_timestamp": timestamp,
        })

    return articles


def fetch_news(category=None, query=None, limit=24):
    if category in RSS_FEEDS:
        categories = [category]
    else:
        categories = list(RSS_FEEDS.keys())

    articles = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        jobs = [
            executor.submit(fetch_feed, source, url, cat)
            for cat in categories
            for source, url in RSS_FEEDS[cat]
        ]

        for job in as_completed(jobs):
            try:
                articles.extend(job.result())
            except Exception as error:
                print(f"Feed unavailable: {error}")

    if query:
        term = query.lower()
        articles = [
            article for article in articles
            if term in (
                article["title"] + " " + article["description"]
            ).lower()
        ]

    unique_articles = []
    seen = set()

    for article in articles:
        key = re.sub(
            r"[^a-z0-9]",
            "",
            article["title"].lower()
        )

        if key and key not in seen:
            seen.add(key)
            unique_articles.append(article)

    unique_articles.sort(
        key=lambda article: article["_timestamp"],
        reverse=True
    )

    result = unique_articles[:max(0, limit)]

    for article in result:
        article.pop("_timestamp", None)

    return result

from flask import Flask, render_template
import urllib.request
import xml.etree.ElementTree as ET

app = Flask(__name__)

FEED_URL = "https://feeds.bbci.co.uk/news/world/rss.xml"


def get_news():
    request = urllib.request.Request(
        FEED_URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        root = ET.fromstring(response.read())

    articles = []

    for item in root.findall(".//item")[:20]:
        articles.append({
            "title": item.findtext("title", "Untitled"),
            "link": item.findtext("link", "#"),
            "description": item.findtext("description", "")
        })

    return articles


@app.route("/")
def home():
    error = None

    try:
        articles = get_news()
    except Exception:
        articles = []
        error = "Could not load news. Please refresh and try again."

    return render_template(
        "index.html",
        articles=articles,
        error=error
    )


if __name__ == "__main__":
    app.run(debug=True)

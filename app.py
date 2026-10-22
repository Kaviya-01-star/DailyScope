from flask import Flask, render_template, request
from news_agent import fetch_news

app = Flask(__name__, template_folder="Templates")


@app.route("/")
def home():
    category = request.args.get("category", "").strip() or None
    query = request.args.get("q", "").strip() or None

    articles = fetch_news(
        category=category,
        query=query,
        limit=24
    )

    return render_template(
        "index.html",
        articles=articles,
        category=category or "",
        query=query or ""
    )


if __name__ == "__main__":
    app.run(debug=True)
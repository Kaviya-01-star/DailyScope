
import urllib.request
import xml.etree.ElementTree as ET

URL = "https://feeds.bbci.co.uk/news/world/rss.xml"

def get_news():
    print("\n🌍 WORLD NEWS\n")

    try:
        request = urllib.request.Request(
            URL,
            headers={"User-Agent": "AI-News-Agent/1.0"}
        )

        with urllib.request.urlopen(request, timeout=15) as response:
            data = response.read()

        root = ET.fromstring(data)
        items = root.findall(".//item")

        for i, item in enumerate(items[:10], 1):
            title = item.findtext("title", "No title")
            link = item.findtext("link", "")

            print(f"{i}. {title}")
            print(f"   {link}\n")

    except Exception as error:
        print("Could not fetch news:", error)

if __name__ == "__main__":
    get_news()

import argparse
import csv
from pathlib import Path
import re
import time

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
OUTPUT_FILE = DATA_DIR / "dataset_final.csv"
HEADERS = {"User-Agent": "Mozilla/5.0"}
SOURCES = {
    "Gazeta Shqiptare": ("gazetashqiptare_all_article_urls.txt", r"(entry-content|td-post-content|post-content)"),
    "Panorama": ("panorama_urls.txt", r"(entry-content|post-content|article-body|single-content)"),
    "Telegrafi": ("telegrafi_news_article_urls.txt", r"(article-body|single-content|post-content)"),
}


def clean_soup(soup):
    for tag in soup(["header", "footer", "nav", "aside", "script", "style", "form", "iframe"]):
        tag.decompose()
    for element in soup.find_all(class_=re.compile(r"(sidebar|comment|related|widget|share|advert)", re.I)):
        element.decompose()


def extract_article(session, url, content_pattern):
    try:
        response = session.get(url, headers=HEADERS, timeout=(5, 20))
        if response.status_code != 200:
            return None, None
        soup = BeautifulSoup(response.text, "html.parser")
        title_node = soup.find("meta", property="og:title") or soup.find("h1")
        if not title_node:
            return None, None
        title = title_node.get("content", "") if title_node.name == "meta" else title_node.get_text(" ", strip=True)
        title = re.sub(r"\s*[-|]\s*(Panorama|Telegrafi|Gazeta Shqiptare).*", "", title, flags=re.I).strip()
        clean_soup(soup)
        content = soup.find("div", class_=re.compile(content_pattern, re.I)) or soup.find("article")
        if not content:
            return None, None
        paragraphs = []
        for paragraph in content.find_all("p"):
            text = re.sub(r"\s+", " ", paragraph.get_text(" ", strip=True)).strip()
            if len(text) >= 35:
                paragraphs.append(text)
        article_text = " ".join(paragraphs)
        if title and len(article_text) > 150:
            return title, article_text
    except requests.RequestException:
        pass
    return None, None


def read_existing_urls():
    if not OUTPUT_FILE.exists():
        return set()
    with OUTPUT_FILE.open("r", encoding="utf-8", newline="") as file:
        return {row[2] for row in csv.reader(file) if len(row) >= 3 and row[2] != "url"}


def scrape(max_per_site, reset):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    existing_urls = set() if reset else read_existing_urls()
    mode = "w" if reset or not OUTPUT_FILE.exists() else "a"
    with OUTPUT_FILE.open(mode, newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if mode == "w":
            writer.writerow(["target_summary", "source_text", "url"])
        with requests.Session() as session:
            for source, (filename, content_pattern) in SOURCES.items():
                url_file = DATA_DIR / "urls" / filename
                if not url_file.exists():
                    print(f"[SKIP] Mungon {url_file}")
                    continue
                urls = [line.strip() for line in url_file.read_text(encoding="utf-8").splitlines() if line.strip()]
                saved = 0
                for url in urls:
                    if saved >= max_per_site or url in existing_urls:
                        continue
                    title, content = extract_article(session, url, content_pattern)
                    if title and content:
                        writer.writerow([title, content, url])
                        file.flush()
                        existing_urls.add(url)
                        saved += 1
                        print(f"[{source} {saved}/{max_per_site}] {title[:60]}")
                    time.sleep(0.15)
                print(f"[OK] {source}: {saved} artikuj të rinj")


def main():
    parser = argparse.ArgumentParser(description="Shkarkon dhe ruan artikuj nga portalet shqiptare.")
    parser.add_argument("--max-per-site", type=int, default=3500)
    parser.add_argument("--reset", action="store_true", help="Rikrijon dataset_final.csv nga e para.")
    args = parser.parse_args()
    scrape(args.max_per_site, args.reset)


if __name__ == "__main__":
    main()
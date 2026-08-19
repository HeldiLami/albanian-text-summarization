from pathlib import Path
from urllib.parse import urlparse
import re
import time

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw_sitemaps"
URL_DIR = ROOT / "data" / "urls"
HEADERS = {"User-Agent": "Mozilla/5.0"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def local_locs(path):
    if not path.exists():
        return []
    soup = BeautifulSoup(path.read_bytes(), "xml")
    return [tag.get_text(strip=True) for tag in soup.find_all("loc")]


def remote_locs(url):
    response = SESSION.get(url, timeout=(5, 30))
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "xml")
    return [tag.get_text(strip=True) for tag in soup.find_all("loc")]


def is_article_url(url):
    parsed = urlparse(url)
    path = parsed.path.lower().strip("/")
    if not parsed.scheme or not parsed.netloc or not path:
        return False
    if any(part in path for part in ("media-library", "category/", "about-us", "contact", "privacy", "tv/", "author/", "tag/")):
        return False
    if re.search(r"\.(jpg|jpeg|png|webp|gif|svg|pdf)(?:$|/)", path):
        return False
    if "gazetashqiptare.al" in parsed.netloc:
        return bool(re.match(r"^\d{4}/\d{2}/\d{2}/.+$", path))
    return True


def unique_articles(urls):
    result = []
    seen = set()
    for url in urls:
        normalized = url.strip()
        if normalized and normalized not in seen and is_article_url(normalized):
            seen.add(normalized)
            result.append(normalized)
    return result


def write_urls(filename, urls):
    output_path = URL_DIR / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(urls) + ("\n" if urls else ""), encoding="utf-8")
    print(f"[OK] {filename}: {len(urls)} artikuj")


def collect_gazetashqiptare():
    sitemap_urls = [
        url for url in local_locs(RAW_DIR / "gazetashqiptare_index.xml")
        if "post-sitemap" in url
    ]
    existing_path = URL_DIR / "gazetashqiptare_all_article_urls.txt"
    article_urls = existing_path.read_text(encoding="utf-8").splitlines() if existing_path.exists() else []
    for index, sitemap_url in enumerate(sitemap_urls, start=1):
        for attempt in range(1, 4):
            try:
                article_urls.extend(remote_locs(sitemap_url))
                print(f"Gazeta Shqiptare {index}/{len(sitemap_urls)}")
                break
            except requests.RequestException as error:
                print(f"[RETRY {attempt}/3] {sitemap_url}: {error}")
                if attempt == 3:
                    print(f"[SKIP] {sitemap_url}")
        if index % 10 == 0:
            write_urls("gazetashqiptare_all_article_urls.txt", unique_articles(article_urls))
        time.sleep(0.1)
    write_urls("gazetashqiptare_all_article_urls.txt", unique_articles(article_urls))


def collect_telegrafi():
    sitemap_path = RAW_DIR / "telegrafi_news.xml"
    sitemap_urls = local_locs(sitemap_path)
    if not sitemap_urls:
        sitemap_urls = [
            url for url in local_locs(RAW_DIR / "telegrafi_sitemap.xml")
            if "news" in url.lower()
        ]
    if not sitemap_urls:
        fallback_path = URL_DIR / "telegrafi_news_sub.txt"
        if fallback_path.exists():
            sitemap_urls = [
                line.strip() for line in fallback_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
    article_urls = []
    for sitemap_url in sitemap_urls:
        try:
            article_urls.extend(remote_locs(sitemap_url))
        except requests.RequestException as error:
            print(f"[ERROR] {sitemap_url}: {error}")
    write_urls("telegrafi_news_article_urls.txt", unique_articles(article_urls))


def main():
    panorama_urls = unique_articles(local_locs(RAW_DIR / "panorama_sitemap.xml"))
    write_urls("panorama_urls.txt", panorama_urls)
    collect_gazetashqiptare()
    collect_telegrafi()


if __name__ == "__main__":
    main()
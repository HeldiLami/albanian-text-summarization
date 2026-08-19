from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "raw_sitemaps"
HEADERS = {"User-Agent": "Mozilla/5.0"}
SITEMAPS = {
    "panorama_sitemap.xml": "https://www.panorama.com.al/sitemap.xml",
    "gazetashqiptare_index.xml": "https://gazetashqiptare.al/sitemap_index.xml",
    "telegrafi_sitemap.xml": "https://telegrafi.com/sitemap.xml",
    "telegrafi_news.xml": "https://telegrafi.com/sitemap_news.xml",
}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, url in SITEMAPS.items():
        try:
            response = requests.get(url, headers=HEADERS, timeout=20)
            response.raise_for_status()
            output_path = OUTPUT_DIR / filename
            output_path.write_bytes(response.content)
            print(f"[OK] {filename}: {len(response.content)} bytes")
        except requests.RequestException as error:
            print(f"[ERROR] {filename}: {error}")


if __name__ == "__main__":
    main()
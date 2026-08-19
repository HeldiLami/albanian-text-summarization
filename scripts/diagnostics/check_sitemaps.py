from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw_sitemaps"


for sitemap in sorted(RAW_DIR.glob("*.xml")):
    soup = BeautifulSoup(sitemap.read_bytes(), "xml")
    print(f"{sitemap.name}: {len(soup.find_all('loc'))} URL")
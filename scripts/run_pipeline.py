import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def run_script(filename, *arguments):
    subprocess.run([sys.executable, str(ROOT / "scripts" / filename), *arguments], check=True)


def main():
    parser = argparse.ArgumentParser(description="Ekzekuton gjithë pipeline-in e dataset-it.")
    parser.add_argument("--max-per-site", type=int, default=3500)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    run_script("download_sitemaps.py")
    run_script("build_article_urls.py")
    scraper_args = ["--max-per-site", str(args.max_per_site)]
    if args.reset:
        scraper_args.append("--reset")
    run_script("scrape_articles.py", *scraper_args)


if __name__ == "__main__":
    main()
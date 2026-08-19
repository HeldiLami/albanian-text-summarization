import csv
import requests
from bs4 import BeautifulSoup
import re

HEADERS = {"User-Agent": "Mozilla/5.0"}

# Merr 5 URL te Telegrafit qe s'jane akoma ne dataset
with open("data/urls/telegrafi_news_article_urls.txt", "r", encoding="utf-8") as f:
    telegrafi_urls = [line.strip() for line in f if line.strip()][:5]

print(f"Total URL telegrafi ne skedar: {len(open('data/urls/telegrafi_news_article_urls.txt', encoding='utf-8').readlines())}")
print("\n--- Testim direkt i 5 URL-ve te para ---\n")

for url in telegrafi_urls:
    print(f"URL: {url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        print(f"  Status: {r.status_code}")
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            
            title_node = soup.find("meta", property="og:title") or soup.find("h1")
            print(f"  Titull gjetur: {'PO' if title_node else 'JO'}")
            
            content = soup.find("div", class_=re.compile(r"(article-body|single-content|post-content)", re.I))
            print(f"  Content div gjetur: {'PO' if content else 'JO'}")
            
            if content:
                paragraphs = content.find_all("p")
                print(f"  Numri i <p>: {len(paragraphs)}")
    except Exception as e:
        print(f"  GABIM: {type(e).__name__}: {e}")
    print()
import requests


URLS = {
    "Panorama": "https://www.panorama.com.al/",
    "Gazeta Shqiptare": "https://gazetashqiptare.al/",
    "Telegrafi": "https://telegrafi.com/",
}


for source, url in URLS.items():
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        print(f"{source}: {response.status_code} ({len(response.content)} bytes)")
    except requests.RequestException as error:
        print(f"{source}: ERROR ({error})")
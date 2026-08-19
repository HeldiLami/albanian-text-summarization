import csv
from collections import Counter

with open("data/dataset_final.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)  # skip header
    sources = Counter()
    for row in reader:
        url = row[2]
        if "gazetashqiptare" in url:
            sources["Gazeta Shqiptare"] += 1
        elif "panorama" in url:
            sources["Panorama"] += 1
        elif "telegrafi" in url:
            sources["Telegrafi"] += 1

for source, count in sources.items():
    print(f"{source}: {count}")
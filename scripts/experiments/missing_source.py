import csv
from collections import Counter

with open("data/dataset_final.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    print("Header:", header)
    
    total = 0
    unmatched = []
    sources = Counter()
    
    for row in reader:
        total += 1
        if len(row) < 3:
            print("RRESHT I PADEFORMUAR:", row)
            continue
        url = row[2]
        if "gazetashqiptare" in url:
            sources["Gazeta Shqiptare"] += 1
        elif "panorama" in url:
            sources["Panorama"] += 1
        elif "telegrafi" in url:
            sources["Telegrafi"] += 1
        else:
            unmatched.append(url)

print(f"\nTotal rreshta: {total}")
print(f"Te panjohur (unmatched): {len(unmatched)}")
print("\nShembuj URL te panjohur (10 te para):")
for u in unmatched[:10]:
    print(" ", u)
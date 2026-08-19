import re
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split

# Since the file is located directly in the "scripts/" folder, we use parents[1]
ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "data" / "dataset_final.csv"
OUTPUT_DIR = ROOT / "data" / "processed"
UPPER_BOUND = 1000


def clean_raw_text(text):
    if not isinstance(text, str):
        return ""

    # Remove remaining HTML entities (e.g., &nbsp;, &amp;)
    text = re.sub(r"&[a-zA-Z]+;", " ", text)

    # Remove standard noisy portal phrases/boilerplate text
    noise_patterns = [
        r"Ndiqni\s+.*?\s+në\s+Facebook",
        r"Lexo\s+edhe\s*:.*",
        r"Foto\s*:\s*.*",
        r"Burimi\s*:\s*.*",
        r"Shpërndaje\s+këtë\s+lajm",
        r"Ju ftojmë të diskutoni.*",
    ]
    for pattern in noise_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Standardize whitespace (remove duplicate spaces)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_source(url):
    if "gazetashqiptare" in url:
        return "gazetashqiptare"
    elif "panorama" in url:
        return "panorama"
    elif "telegrafi" in url:
        return "telegrafi"
    return "unknown"


def main():
    if not INPUT_FILE.exists():
        print(f"[ERROR] File {INPUT_FILE} not found! (Please wait for the scraping to finish)")
        return

    print("---> Reading initial dataset...")
    df = pd.read_csv(INPUT_FILE)
    print(f"Initial rows: {len(df)}")

    print("---> Cleaning text contents (this will take a few seconds)...")
    df["target_summary"] = df["target_summary"].apply(clean_raw_text)
    df["source_text"] = df["source_text"].apply(clean_raw_text)

    print("---> Removing duplicates...")
    df = df.drop_duplicates(subset=["url"])
    df = df.drop_duplicates(subset=["source_text"])
    df = df.drop_duplicates(subset=["target_summary"])
    print(f"Rows after removing duplicates: {len(df)}")


    print("---> Filtering by word length...")
    df["summary_len"] = df["target_summary"].apply(lambda x: len(x.split()))
    df["source_len"] = df["source_text"].apply(lambda x: len(x.split()))

    # Keep articles where source_text >= 40 words and target_summary >= 3 words
    df_clean = df[
        (df["source_len"] >= 40) & 
        (df["source_len"] <= UPPER_BOUND) & 
        (df["summary_len"] >= 3)
    ].copy()    
    # Drop auxiliary length calculation columns
    df_clean = df_clean.drop(columns=["summary_len", "source_len"])
    print(f"Valid rows for training: {len(df_clean)}")

    # Shto kolonen 'source' per stratifikim
    df_clean["source"] = df_clean["url"].apply(get_source)
    print("\nShperndarja sipas burimit:")
    print(df_clean["source"].value_counts())
    
    print(f"Valid rows for training: {len(df_clean)}")

    print("---> Splitting dataset (80% Train, 10% Val, 10% Test)...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("---> Splitting dataset (80% Train, 10% Val, 10% Test)...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    train_df, test_val_df = train_test_split(
        df_clean, test_size=0.20, random_state=42, stratify=df_clean["source"]
    )
    val_df, test_df = train_test_split(
        test_val_df, test_size=0.50, random_state=42, stratify=test_val_df["source"]
    )

    df_clean = df_clean.drop(columns=["source"])
    train_df = train_df.drop(columns=["source"])
    val_df = val_df.drop(columns=["source"])
    test_df = test_df.drop(columns=["source"])

    # Save processed splits
    df_clean.to_csv(OUTPUT_DIR / "cleaned_dataset.csv", index=False, encoding="utf-8")
    train_df.to_csv(OUTPUT_DIR / "train.csv", index=False, encoding="utf-8")
    val_df.to_csv(OUTPUT_DIR / "val.csv", index=False, encoding="utf-8")
    test_df.to_csv(OUTPUT_DIR / "test.csv", index=False, encoding="utf-8")

    print("\n[SUCCESS] Dataset successfully cleaned and split!")
    print(f" Saved under directory: data/processed/")
    print(f" --------------------------------")
    print(f" Training Set (Train):       {len(train_df)}")
    print(f" Validation Set (Val):       {len(val_df)}")
    print(f" Testing Set (Test):         {len(test_df)}")


if __name__ == "__main__":
    main()
import pandas as pd
from transformers import AutoTokenizer

MODEL_NAME = "google/mt5-small"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

train_df = pd.read_csv("data/processed/train.csv")
sample = train_df["source_text"].sample(500, random_state=42)

for max_len in [256, 384, 512, 640]:
    truncated = sample.apply(
        lambda t: len(tokenizer.tokenize(t)) > max_len
    ).mean()
    print(f"max_length={max_len}: {truncated:.1%} of articles are cut")
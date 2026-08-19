import pandas as pd

df = pd.read_csv("data/processed/cleaned_dataset.csv")
df["source_len"] = df["source_text"].apply(lambda x: len(x.split()))
df["summary_len"] = df["target_summary"].apply(lambda x: len(x.split()))

print(df[["source_len", "summary_len"]].describe())

# Leakage check - how often is the summary literally inside the source text?
leak_count = sum(df["target_summary"].str[:50].apply(lambda s: s in df["source_text"].iloc[0]) for _ in [0])
overlap = (df.apply(lambda row: row["target_summary"][:60] in row["source_text"], axis=1)).mean()
print(f"\n% of rows where summary is verbatim substring of source: {overlap:.1%}")
print(df["source_len"].quantile([0.90, 0.95, 0.99]))
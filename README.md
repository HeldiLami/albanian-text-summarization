# Albanian Text Summarization

An end-to-end research project for abstractive news summarization in Albanian. It collects Albanian news articles, cleans and splits the data, fine-tunes `google/mt5-small` with LoRA, and evaluates the resulting model against Lead-N baselines.

The final model is available locally in `models/mt5-shqip-LoRA/` as a PEFT adapter. The project documentation and experiment log are in [`documentation.md`](documentation.md).

## Results

Evaluation was performed on a held-out test set of 1,683 examples:

| Method               |   ROUGE-1 |  ROUGE-2 |   ROUGE-L |
| -------------------- | --------: | -------: | --------: |
| Lead-8               |     18.35 |     5.79 |     15.99 |
| Lead-12              |     21.87 |     7.04 |     18.21 |
| Lead-20              |     23.93 |     8.07 |     18.86 |
| **mT5-small + LoRA** | **25.47** | **9.27** | **21.00** |

The model was trained for five epochs with `bf16` mixed precision. Generation uses beam search with repetition controls to reduce duplicated phrases.

## Dataset

The collected dataset is stored in `data/dataset_final.csv` and contains articles from:

- Gazeta Shqiptare
- Panorama
- Telegrafi

The processed dataset contains 16,824 examples after cleaning, deduplication, length filtering, and a stratified split by source:

| Split      | Examples |
| ---------- | -------: |
| Train      |   13,459 |
| Validation |    1,682 |
| Test       |    1,683 |

Processed files are in `data/processed/`. Each row contains `target_summary`, `source_text`, and `url`.

## Setup

Python 3.10+ is recommended. Install the packages used by the scripts and notebook:

```powershell
python -m pip install -r requirements.txt
```

The repository currently contains the processed data locally, but the CSV files are excluded from Git because the dataset is larger than the practical GitHub file-size limit. Download or copy the data into `data/` before running preprocessing or the training notebook. The LoRA adapter files must also be present in `models/mt5-shqip-LoRA/` for local inference.

## Data collection

Run these commands from the project root:

```powershell
python scripts/run_pipeline.py --max-per-site 3500
```

The orchestrator runs the following steps:

1. `scripts/scrapers/download_sitemaps.py` downloads sitemap files to `data/raw_sitemaps/`.
2. `scripts/scrapers/build_article_urls.py` extracts article URLs into `data/urls/`.
3. `scripts/scrapers/scrape_articles.py` downloads article titles and text into `data/dataset_final.csv`.

The scraper is resumable and skips URLs already present in the CSV. To recreate the output file:

```powershell
python scripts/run_pipeline.py --reset --max-per-site 3500
```

For a minimal connectivity/scraping check:

```powershell
python scripts/scrapers/scrape_articles.py --max-per-site 1
```

The checked-in final dataset was collected from all three sources. The current scraper configuration is intentionally limited to Telegrafi in `scripts/scrapers/scrape_articles.py`; enable the other source entries there before running a new multi-source collection.

## Preprocessing

Clean and split the collected CSV with:

```powershell
python scripts/clean_dataset.py
```

The script removes portal boilerplate and duplicates, keeps source texts between 40 and 1,000 words, requires summaries of at least three words, and creates an 80/10/10 stratified train/validation/test split.

## Inference

The LoRA adapter requires the base mT5 model. A GPU is recommended, but the device can be changed to `cpu` for a slower local run:

```python
import torch
from peft import PeftModel
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

base_name = "google/mt5-small"
adapter_path = "models/mt5-shqip-LoRA"
device = "cuda" if torch.cuda.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained(adapter_path)
base_model = AutoModelForSeq2SeqLM.from_pretrained(base_name)
model = PeftModel.from_pretrained(base_model, adapter_path).merge_and_unload()
model.to(device).eval()

article = "Vendosni këtu tekstin e artikullit në shqip."
inputs = tokenizer(article, max_length=640, truncation=True, return_tensors="pt").to(device)

with torch.no_grad():
		output = model.generate(
				**inputs,
				max_length=96,
				num_beams=4,
				no_repeat_ngram_size=2,
				repetition_penalty=1.12,
				length_penalty=1.2,
				early_stopping=True,
		)

print(tokenizer.decode(output[0], skip_special_tokens=True))
```

## Training and experiments

- `scripts/modeltrain.ipynb` contains the tokenization, LoRA fine-tuning, evaluation, and baseline comparison workflow.
- `scripts/experiments/` contains dataset statistics, source-distribution checks, and token-length experiments.
- `scripts/diagnostics/` contains connectivity and sitemap checks.

The notebook was developed on Kaggle with internet and GPU access. It can also run from the repository root after the dependencies, processed CSV files, and model adapter have been made available locally.

## Repository structure

```text
data/
	dataset_final.csv                 # Raw collected dataset
	processed/                        # Cleaned train/validation/test splits
	test_predictions_with_summaries.csv
	raw_sitemaps/                     # Downloaded sitemap files
	urls/                             # Extracted article URL lists
models/mt5-shqip-LoRA/              # Fine-tuned LoRA adapter and tokenizer
scripts/
	clean_dataset.py                  # Cleaning and stratified splitting
	run_pipeline.py                   # Collection orchestrator
	modeltrain.ipynb                  # Training and evaluation notebook
	scrapers/                         # Sitemap, URL, and article collection
	diagnostics/                      # Pipeline diagnostics
	experiments/                      # Analysis scripts
documentation.md                   # Detailed project log and methodology
```

## Limitations

This is a single-source-news summarization model trained on portal articles and lead-style reference summaries. ROUGE does not fully measure factuality, grammar, or editorial quality, so generated summaries should also be reviewed manually. The model is not intended for translation, multi-document summarization, or answering questions outside the supplied article context.

## License

The adapter metadata specifies the Apache 2.0 license. Check the terms of the original news sources and the `google/mt5-small` model before redistributing collected data or deploying the complete system.

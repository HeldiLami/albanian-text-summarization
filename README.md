# Albanian Text Summarization

This project collects articles from Panorama, Gazeta Shqiptare, and Telegrafi and stores them in `data/dataset_final.csv`.

## Pipeline

From the project root:

```powershell
python scripts/run_pipeline.py --max-per-site 3500
```

The steps are:

1. `scripts/download_sitemaps.py` downloads the sitemaps to `data/raw_sitemaps/`.
2. `scripts/build_article_urls.py` creates clean URL lists in `data/urls/`.
3. `scripts/scrape_articles.py` downloads the articles and continues from any missing URLs.

To create the dataset from scratch, use:

```powershell
python scripts/run_pipeline.py --reset --max-per-site 3500
```

For a small test run:

```powershell
python scripts/scrape_articles.py --max-per-site 1
```

Diagnostics can be found in `scripts/diagnostics/`.

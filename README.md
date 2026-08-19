# Diploma Article Dataset

Ky projekt mbledh artikuj nga Panorama, Gazeta Shqiptare dhe Telegrafi dhe i ruan te `data/dataset_final.csv`.

## Pipeline

Nga rrënja e projektit:

```powershell
python scripts/run_pipeline.py --max-per-site 3500
```

Hapat janë:

1. `scripts/download_sitemaps.py` shkarkon sitemap-et te `data/raw_sitemaps/`.
2. `scripts/build_article_urls.py` krijon lista të pastra URL-sh te `data/urls/`.
3. `scripts/scrape_articles.py` shkarkon artikujt dhe vazhdon nga URL-të që mungojnë.

Për ta krijuar dataset-in nga e para përdor:

```powershell
python scripts/run_pipeline.py --reset --max-per-site 3500
```

Për një provë të vogël:

```powershell
python scripts/03_scrape_articles.py --max-per-site 1
```

Diagnostika gjendet te `scripts/diagnostics/`.

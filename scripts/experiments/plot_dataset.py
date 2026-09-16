"""Create thesis figures from the saved cleaned corpus; never modify the data."""
from pathlib import Path
from urllib.parse import urlparse
import hashlib
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / 'data/processed/cleaned_dataset.csv'
OUTPUT = ROOT / 'data/figures'
PORTALS = {'gazetashqiptare.al': 'Gazeta Shqiptare', 'telegrafi.com': 'Telegrafi', 'panorama.com.al': 'Panorama'}


def main():
    df = pd.read_csv(INPUT)
    if df[['source_text', 'target_summary', 'url']].isna().any().any():
        raise ValueError('Missing text or URL: inspect the corpus before plotting.')
    df['portal'] = df.url.map(lambda value: PORTALS[urlparse(value).hostname.removeprefix('www.')])
    df['article_words'] = df.source_text.str.split().str.len()
    df['title_words'] = df.target_summary.str.split().str.len()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Serif', 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    stats = {'rows': len(df), 'input_sha256': hashlib.sha256(INPUT.read_bytes()).hexdigest(),
             'word_count': 'whitespace-separated units; no model tokenizer',
             'pearson_r': float(df.article_words.corr(df.title_words)), 'portals': {}}
    groups, labels = [], []
    for portal in PORTALS.values():
        values = df.loc[df.portal == portal, 'article_words']
        groups.append(values.to_numpy())
        labels.append(f'{portal}\n(n = {len(values):,})'.replace(',', ' '))
        stats['portals'][portal] = {'n': len(values), 'median': float(values.median()), 'q1': float(values.quantile(.25)), 'q3': float(values.quantile(.75))}
    fig, ax = plt.subplots(figsize=(7.2, 4.5), layout='constrained')
    ax.boxplot(groups, tick_labels=labels, widths=.5, whis=1.5, patch_artist=True,
               boxprops={'facecolor': '#dddddd', 'edgecolor': '#444444'},
               medianprops={'color': '#111111', 'linewidth': 1.6},
               whiskerprops={'color': '#555555'}, capprops={'color': '#555555'},
               flierprops={'marker': 'o', 'markersize': 2, 'alpha': .22, 'markeredgecolor': '#555555'})
    ax.set_ylabel('Gjatësia e artikullit (fjalë)')
    ax.set_ylim(0, 1050)
    ax.grid(axis='y', color='#e6e6e6', linewidth=.6)
    ax.set_axisbelow(True)
    for ext in ['png', 'svg']:
        fig.savefig(OUTPUT / f'boxplot_gjatesia_sipas_portalit.{ext}', dpi=300)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.2, 4.5), layout='constrained')
    ax.scatter(df.article_words, df.title_words, s=5, alpha=.10, color='#333333', edgecolors='none', rasterized=True)
    ax.set_xlabel('Gjatësia e artikullit (fjalë)')
    ax.set_ylabel('Gjatësia e titullit referues (fjalë)')
    ax.set_xlim(0, 1050)
    ax.set_ylim(0, 42)
    ax.grid(color='#e6e6e6', linewidth=.6)
    ax.set_axisbelow(True)
    ax.text(.98, .97, f'n = {len(df):,}\nr = {stats["pearson_r"]:.3f}'.replace(',', ' ').replace('.', ','), transform=ax.transAxes, ha='right', va='top')
    for ext in ['png', 'svg']:
        fig.savefig(OUTPUT / f'scatter_artikull_titull.{ext}', dpi=300)
    plt.close(fig)
    (OUTPUT / 'plot_statistics.json').write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(stats, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()

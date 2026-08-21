# Dokumentim i Progresit — Përmbledhje Automatike e Lajmeve Shqip (mT5 + LoRA)

## Qëllimi i temës

Zhvillimi i një modeli për **përmbledhje automatike abstraktive** (abstractive summarization) të artikujve të lajmeve në gjuhën shqipe, duke përdorur fine-tuning të mT5-small me teknikën LoRA (Low-Rank Adaptation). Projekti replikon metodologjinë e XL-Sum (Hasan et al., 2021) të përshtatur për shqipen si gjuhë me pak burime (low-resource language).

---

## Faza 0: Studimi teorik

### Burimet kryesore
- **XL-Sum** (Hasan et al., ACL Findings 2021) — dataset dhe metodologji summarization për 44 gjuhë, bazuar në artikuj BBC dhe paragrafin hyrës si "gold summary"
- Survey mbi automatic text summarization (dl.acm.org/10.1145/3487288) — kontekst i gjerë i fushës

### Konceptet themelore të mësuara
- **CNN/DailyMail vs XSum**: CNN/DM ka summary ekstraktivë dhe të gjatë (bullet points); XSum (paraardhësi i XL-Sum, gjithashtu nga BBC) përdor 1 fjali/paragraf hyrës si summary — shumë më abstractive. Struktura e dataset-it tim (artikull + lead paragraph) ndjek pikërisht modelin XSum/XL-Sum.
- **mT5**: model encoder-decoder, paratrajnuar në 101 gjuhë përmes korpusit mC4, përfshirë shqipen. Kjo justifikon pse fine-tuning me pak të dhëna është i mundshëm — modeli "e njeh" gjuhën që në pretraining.
- **Full fine-tuning vs LoRA/PEFT**: full fine-tuning përditëson gjithë parametrat (~300M për mT5-small), rrezik i lartë overfitting me dataset të vogël + kërkon shumë memorie GPU. LoRA ngrin modelin bazë dhe trajnon vetëm matrica shtesë të vogla (target_modules=["q","v"]) — zgjedhja e justifikuar për kushte praktike (Kaggle T4 GPU falas, dataset low-resource).
- **Baseline standarde**: Lead-N (zakonisht Lead-3) — merr N fjalitë e para të artikullit si "summary" pa asnjë model ML. Shërben si testi minimal çdo model duhet ta kalojë; nëse mT5+LoRA del më keq se Lead-3, fine-tuning s'ka vlerë reale.
- **ROUGE** (ROUGE-1, ROUGE-2, ROUGE-L) — metrika standarde e mbivendosjes n-gram mes tekstit të gjeneruar dhe referencës; duhet kombinuar me inspektim manual sepse ROUGE i lartë s'garanton kuptim gramatikor.

---

## Faza 1: Grumbullimi i të dhënave (Web Scraping)

### Burimet e zgjedhura
Tre portale lajmesh shqip (jo vetëm 1 si XL-Sum me BBC — zgjedhje e ndërgjegjshme për diversitet stili editorial):
- **Panorama.com.al**
- **Gazeta Shqiptare** (gazetashqiptare.al)
- **Telegrafi.com**

### Strategjia: Sitemaps, jo crawling manual
Përdorimi i `sitemap.xml`/`sitemap_index.xml` të secilit sajt për të marrë lista të plota URL-sh artikujsh, në vend të navigimit faqe-për-faqe.

### Gjetjet specifike për secilin burim
| Burim | Strukturë sitemap | Sfida e hasur |
|---|---|---|
| Panorama | Sitemap i vetëm, i përzier (kategori + artikuj + homepage) | Kërkoi filtrim me pattern URL (`/category/` excluded); vetëm ~474 artikuj të disponueshëm (sitemap dukej "dritare rrotulluese", jo arkiv i plotë) |
| Gazeta Shqiptare | Sitemap index → 269 nën-sitemaps `post-sitemap*.xml` (format WordPress) | E thjeshtë të filtrohej me pattern `"post-sitemap"` |
| Telegrafi | Dy sitemaps: `sitemap_news.xml` (arkiv i vogël, ~50 URL) dhe `sitemap.xml` (arkiv i plotë, 25,929 nën-sitemaps, deri ~1.3M artikuj potencialë) | Fillimisht u përdor vetëm sitemap "news" i vogël → rezultoi në vetëm 47 artikuj të scraped. U zgjidh duke kaluar te arkivi i plotë me sampling (random shuffle + target-based collection deri ~7,000 artikuj) |

### Arkitektura e pipeline-it (skriptet)
Struktura finale, e konsoliduar pas disa iterimesh eksperimentale:
```
scripts/
├── run_pipeline.py              # orkestrues (thërret 01→02→03 me subprocess)
└── scrapers/
    ├── 01_download_sitemaps.py  # shkarkon sitemap XML lokalisht
    ├── 02_build_article_urls.py # nxjerr URL artikujsh (me retry logic, checkpoint çdo 10/20 sitemaps)
    └── 03_scrape_articles.py    # HTML → CSV (argparse: --max-per-site, --reset)
```

**Karakteristika teknike të rëndësishme**:
- Idempotencë: kontrollon `existing_urls` para se të rishkarkojë, mund të rifillohet pa dublikime
- `file.flush()` pas çdo rreshti të ruajtur → mbron progresin nëse programi ndërpritet papritur
- Filtër i unifikuar `is_article_url()` — heq faqe kategorish, tag pages, faqe autori, media/imazhe
- Regex content selectors specifikë për secilin burim (`entry-content`, `article-body`, `single-content`, etj.)
- Filtrim zhurme teksti: email-e, "kontakt:", boilerplate komentesh, "ndiqni në Facebook"

### Diagnostikimi i problemeve gjatë scraping
- Testim direkt HTTP status + strukturë HTML për verifikim para se të supozohej "bllokim nga sajti"
- Zbulimi se numri fillestar 47 artikuj për Telegrafin ishte problem **grumbullimi URL-sh** (vetëm 48 URL në skedar), jo problem i vetë scraper-it (i cili funksiononte me ~98% sukses)

---

## Faza 2: Pastrimi dhe përgatitja e dataset-it (`clean_dataset.py`)

### Rrjedha e pastrimit
1. **Leximi** i `dataset_final.csv` (bashkim i të tre burimeve)
2. **Pastrim teksti**: heqje HTML entities, pattern-e boilerplate (Facebook, "Lexo edhe:", "Foto:", "Burimi:"), normalizim hapësirash
3. **Heqje duplikatësh**: mbi `url`, `source_text`, dhe `target_summary` veç e veç
4. **Filtrim sipas gjatësisë**: `source_len >= 40` fjalë, `summary_len >= 3` fjalë
5. **Filtrim outliers**: shtim i kufirit të sipërm `source_len <= 1000` fjalë (bazuar në analizë quantile: 95th percentile = 1030 fjalë; pa këtë filtër kishte artikuj deri 9,613 fjalë që do shtrembëronin trajnimin)
6. **Stratifikim sipas burimit**: split train/val/test (80/10/10) i stratifikuar mbi kolonën `source` (nxjerrë nga URL) për të siguruar proporcione konsistente GSh/Panorama/Telegrafi në të tre ndarjet

### Kontrolli i "leakage" (rrjedhje informacioni)
Verifikuar nëse `target_summary` shfaqet fjalë-për-fjalë brenda `source_text` (do ta bënte detyrën thjesht kopjim, jo summarization real). Rezultat: **0.3%** — praktikisht i papërfillshëm, konfirmon që scraper-i ka ndarë saktë lead paragraph nga trupi i artikullit.

### Statistikat finale të dataset-it
| Metrikë | Vlerë |
|---|---|
| Rreshta fillestarë (bashkuar) | 18,034 |
| Pas heqjes së duplikatëve | 17,915 |
| Pas filtrimit të gjatësisë (me upper bound) | 16,824 |
| **Train** | 13,459 |
| **Validation** | 1,682 |
| **Test** | 1,683 |
| Shpërndarja sipas burimit | Gazeta Shqiptare: 9,675 · Telegrafi: 6,786 · Panorama: 363 |
| source_text (fjalë) — median / mean / max (para upper bound) | 195 / 330 / 9,613 |
| target_summary (fjalë) — median / mean | 12 / 11.9 |

---

## Faza 3: Fine-tuning (mT5-small + LoRA)

### Analiza e tokenizimit (para vendimit të max_length)
Test praktik me `AutoTokenizer.from_pretrained("google/mt5-small")` tregoi raport **~2.1 tokens/fjalë** për shqipen (krahasuar me ~1.3 për anglisht) — shkak: morfologjia e pasur e shqipes (lakim, prapashtesa) e bën SentencePiece tokenizer të ndajë fjalët në shumë nën-copa, pasi mT5 ka pasur ekspozim relativisht të kufizuar ndaj shqipes gjatë pretraining krahasuar me gjuhë "të mëdha".

**Analiza e truncation** në mostër 500 artikujsh:
| max_length | % artikujsh të prera |
|---|---|
| 256 | 71.6% |
| 384 | 44.0% |
| 512 | 30.8% |
| 640 | 22.8% |

**Vendimi**: `MAX_SOURCE_LENGTH = 640`, `MAX_TARGET_LENGTH = 96` — kompromis mes coverage dhe kufizimeve GPU (T4, 16GB VRAM) dhe kuotës kohore Kaggle (~30 orë/javë, session max ~12 orë).

### Konfigurimi LoRA
```python
LoraConfig(
    task_type=TaskType.SEQ_2_SEQ_LM,
    r=16,
    lora_alpha=32,
    lora_dropout=0.1,
    target_modules=["q", "v"],
)
```
Rezultat: **0.12% e parametrave trajnueshëm** (688,128 nga 556,979,584 total — numri total i lartë për shkak të embeddings të "untied" në checkpoint, jo se është mT5-base; është konfirmuar mT5-small).

### Training Arguments (konfigurimi fillestar)
- `learning_rate=1e-3` (më i lartë se full fine-tuning tipik ~1e-5, i justifikuar nga numri shumë i vogël i parametrave trajnueshëm)
- `per_device_train_batch_size=8`
- `fp16=True` (mixed precision për kursim memorie)
- `num_train_epochs=5`
- `metric_for_best_model="rougeL"`, `load_best_model_at_end=True`

### Rezultatet e para 3 epochs (eksperimenti i parë — me problem)
| Epoch | Train Loss | Val Loss | ROUGE-1 | ROUGE-2 | ROUGE-L |
|---|---|---|---|---|---|
| 1 | 2.2027 | 0.8827 | 21.43 | 6.71 | 17.99 |
| 2 | 2.1223 | 0.9523 | 22.40 | 7.51 | 18.92 |
| 3 | 2.1654 | **8.3869** | 21.29 | 7.45 | 18.36 |

### Problemi identifikuar: instabilitet numerik me fp16
Kërcim drastik i Validation Loss (0.95 → 8.39, ~9x) mes epoch 2 dhe 3, ndërkohë Training Loss mbeti stabël. Diagnoza: **instabilitet i njohur i familjes T5/mT5 me mixed precision fp16** — shtresat e T5 janë të ndjeshme ndaj range-it numerik të kufizuar 16-bit, shpesh duke shkaktuar mbi-fluks (overflow) gjatë trajnimit.

**Simptomë shoqëruese**: `compute_metrics` fillimisht dështonte me error gjatë `tokenizer.batch_decode()`, sepse modeli prodhonte token IDs jashtë range-it të vlefshëm (< 0 ose > vocab_size) — pasojë e mundshme e vetë instabilitetit fp16. U shtua clipping mbrojtës:
```python
preds = np.where((preds >= 0) & (preds < tokenizer.vocab_size), preds, tokenizer.pad_token_id)
```
Ky fix e bën kodin të mos dështojë, por **nuk e zgjidh shkakun rrënjësor**.

**Zgjidhja e planifikuar**: kalimi nga `fp16=True` në `bf16=True` (nëse T4 e mbështet) ose `fp32` (fp16=False, bf16=False) si alternativë e sigurt, dhe rifillim i trajnimit nga zero (jo nga checkpoint i epoch 3, i "kontaminuar" nga instabiliteti).

---

## Faza 4: Rifillimi i trajnimit dhe rreziku i humbjes së session-it (mësim operacional)

### Problemi: session Kaggle i humbur
Pas zgjidhjes së problemit fp16 (kalim te `bf16`), trajnimi u rifillua me "Run All" interaktiv (jo "Save & Run All / Commit"). Kur lidhja/PC lokal u ndërpre, **krejt session-i Kaggle u fshi** (jo vetëm humbi lidhja e browser-it) — `/kaggle/working/` u zbraz plotësisht, checkpoint-et dhe objekti `trainer` u humbën, pavarësisht se trajnimi kishte përfunduar me sukses (5/5 epochs, output i plotë i shfaqur).

**Mësim operacional i rëndësishëm**: për trajnime të gjata (>30-60 min) te Kaggle, duhet përdorur gjithmonë **"Save & Run All (Commit)"**, jo ekzekutim interaktiv — commit e ekzekuton notebook si batch job të pavarur nga browser/PC, dhe e ruan output-in (checkpoints, modele) përgjithmonë si pjesë e version-it të commituar.

### Rifillimi i suksesshëm (Training Run 1 — commit)
Trajnimi u rifutur nga zero me `bf16=True` (`fp16=False`), këtë herë si "Save & Run All (Commit)". Rezultati final, 5 epochs, pa asnjë shpërthim numerik:

| Epoch | Train Loss | Val Loss | ROUGE-1 | ROUGE-2 | ROUGE-L |
|---|---|---|---|---|---|
| 1 | 2.9376 | 0.9365 | 14.29 | 3.80 | 12.94 |
| 2 | 2.2768 | 0.8558 | 20.90 | 6.88 | 18.11 |
| 3 | 2.1654 | 0.8036 | 22.16 | 6.97 | 18.47 |
| 4 | 2.0562 | 0.7920 | 23.08 | 7.73 | 19.34 |
| 5 | 2.0532 | 0.7870 | 23.18 | 7.77 | 19.44 |

Train Loss dhe Val Loss bien paralelisht deri në fund (asnjë divergjencë/overfitting), ROUGE-L përmirësohet çdo epoch me lehtë "plateau" drejt fundit (19.34→19.44) — konfirmim i konvergjencës së shëndetshme. Modeli u ruajt (LoRA adapter, `merge_and_unload` opsionale për inference) te output i commit-uar, folder `mt5-shqip-LoRA/`.

---

## Faza 5: Evaluation final mbi Test Set

### Metodologjia
- Ngarkim i modelit nga checkpoint i ruajtur (`PeftModel.from_pretrained` mbi `mt5-small` bazë)
- Gjenerim me beam search (`num_beams=4`) mbi krejt test set (1,683 shembuj)
- Krahasim direkt kundrejt **Lead-N baseline** (N=8, 12, 20 fjalë) mbi të njëjtin test set

### Problem i identifikuar dhe zgjidhur: përsëritje në output (repetition/degeneration)
Inspektimi manual i shembujve fillestarë zbuloi raste output-esh me fraza të përsëritura fjalë-për-fjalë brenda vetes (p.sh. *"i dyshuari kryesor i atentatit në Shkodër, i dyshuari kryesor i atentatit në Shkodër"*) — problem i njohur i beam search generation, jo i vetë modelit/të dhënave. U zgjidh duke shtuar parametra gjenerimi:
```python
model.generate(..., num_beams=4, no_repeat_ngram_size=2,
                repetition_penalty=1.12, length_penalty=1.2, early_stopping=True)
```
Efekti: ROUGE mbeti praktikisht i pandryshuar (siç pritej — ROUGE mat mbivendosje n-gram, jo koherencë), por **cilësia reale e output-it u përmirësua ndjeshëm** (eliminim i plotë i frazave të degjeneruara në shembujt e testuar).

### Rezultatet finale — mT5+LoRA vs Lead-N baseline (Test Set, n=1,683)

| Metodë | ROUGE-1 | ROUGE-2 | ROUGE-L |
|---|---|---|---|
| Lead-8 | 18.35 | 5.79 | 15.99 |
| Lead-12 | 21.87 | 7.04 | 18.21 |
| Lead-20 | 23.93 | 8.07 | 18.86 |
| **mT5-small + LoRA (final)** | **25.47** | **9.27** | **21.00** |

**Konkluzion kryesor**: modeli i fine-tuned tejkalon çdo variant të Lead-N baseline në të tre metrikat ROUGE, me përmirësim ROUGE-L prej **+2.14 pikësh (~11.3% relative)** mbi baseline-in më të fortë (Lead-20). Rezultati bie në zonën "të mirë" krahasuar me referencat e gjuhëve low-resource te XL-Sum paper.

### Gjetje cilësore nga inspektimi manual
- Modeli kap saktë temën/faktin kryesor në shumicën e shembujve (p.sh. "Nancy Reagan vdiq në Bel Air" — fakt korrekt dhe konciz)
- Diferencë stili e vërejtur: `target_summary` (lead paragraph i portaleve) shpesh ka ton "titull klikbait/editorial" (p.sh. "Vrau kushëririn se i shau gruan, shokon para gjykatës"), ndërsa modeli prodhon përmbledhje më faktike/neutrale — diferencë legjitime stili, jo domosdoshmërisht "gabim", por pikë për diskutim në kapitullin e rezultateve
- ROUGE-L në test set (21.00) doli pak **më i lartë** se ai në validation (19.44 në epoch final) — shenjë e mirë, modeli s'ka overfit specifikisht ndaj validation set

---

## Statusi aktual dhe hapat e ardhshëm

**✅ Përfunduar**: studim teorik bazë, grumbullim + pastrim dataset (16,824 shembuj, i stratifikuar), fine-tuning i plotë mT5-small+LoRA (5 epochs, bf16, i qëndrueshëm), evaluation i plotë mbi test set, krahasim me Lead-N baseline, korrigjim i cilësisë së gjenerimit (repetition fix), inspektim manual.

**⏭️ Hapat e ardhshëm**:
1. Shkrimi i kapitullit "Related Work" bazuar në XL-Sum + survey ACM
2. Shkrimi i kapitullit "Metodologji" bazuar në këtë dokument
3. Shkrimi i kapitullit "Rezultate dhe Diskutim" — tabela krahasuese + analiza cilësore + diskutim i sfidave teknike (fp16 instability, humbja e session-it, repetition fix)
4. Organizimi i repository-t GitHub (README me statistika, rezultate, shembuj) për CV/portofol
5. (Opsionale) Eksperimente shtesë: rank LoRA të ndryshëm, krahasim me mT5-base, analizë e gabimeve sipas burimit (GSh vs Panorama vs Telegrafi)

---

*Dokumenti u përgatit si log kronologjik pune, për t'u përdorur si bazë për kapitujt e temës së diplomës (Metodologji, Rezultate, Diskutim i sfidave teknike).*

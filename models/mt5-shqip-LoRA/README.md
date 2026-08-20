---
base_model: google/mt5-small
library_name: peft
tags:
  - base_model:adapter:google/mt5-small
  - lora
  - transformers
  - text-summarization
  - albanian
  - nlp
language:
  - sq
license: apache-2.0
metrics:
  - rouge
pipeline_tag: text2text-generation
---

# mT5-small for Albanian Automatic Text Summarization (LoRA)

This repository contains the fine-tuned LoRA (Low-Rank Adaptation) adapter weights for **`google/mt5-small`**, optimized specifically for abstractive automatic text summarization in the Albanian language.

## Model Details

### Model Description

- **Developed by:** Heldi Lami
- **Model type:** Sequence-to-Sequence Language Model (PEFT / LoRA)
- **Language(s) (NLP):** Albanian (`sq`)
- **License:** Apache 2.0
- **Finetuned from model:** `google/mt5-small`

### Model Sources

- **Repository:** [github.com/HeldiLami/albanian-text-summarization](https://github.com/HeldiLami/albanian-text-summarization)

## Uses

### Direct Use

This model is designed to generate concise single-sentence summaries and news headlines from long-form Albanian news articles and general prose.

### Out-of-Scope Use

The model is not intended for multi-document summarization, text translation, or factual query answering outside the scope of the provided context.

## How to Get Started with the Model

Use the code below to load the model with PEFT adapters and run inference on GPU:

```python
import torch
from peft import PeftModel
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

MODEL_NAME = "google/mt5-small"
LORA_PATH = "models/mt5-shqip-LoRA"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Load tokenizer and base model
tokenizer = AutoTokenizer.from_pretrained(LORA_PATH)
base_model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

# Load PEFT adapters and merge weights
model = PeftModel.from_pretrained(base_model, LORA_PATH)
model = model.merge_and_unload()
model.eval().to(DEVICE)

# Run inference
article_text = "Insert text in Albanian..."
inputs = tokenizer(article_text, max_length=640, truncation=True, return_tensors="pt").to(DEVICE)

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_length=96,
        num_beams=4,
        length_penalty=1.2,
        no_repeat_ngram_size=2,
        repetition_penalty=1.12,
        early_stopping=True
    )

summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
print("Summary:", summary)
```

## Training Details

### Training Data

Trained on an Albanian news dataset split into standard training (`train`), validation (`val`), and testing (`test`) subsets.

### Training Procedure

#### Preprocessing

- **Max Source Length:** 640 tokens
- **Max Target Length:** 96 tokens
- **Tokenization:** `google/mt5-small` SentencePiece tokenizer

#### Training Hyperparameters

- **Adapter Configuration:** LoRA (r=16, alpha=32, `lora_dropout=0.1`)
- **Target Modules:** Query (`q`) and Value (`v`) projections
- **Epochs:** 5
- **Learning Rate:** 1e-3
- **Batch Size:** 8 per device
- **Optimizer / Precision:** Weight decay = 0.01, `bf16` mixed precision
- **Best Model Selection:** Metric-based (ROUGE-L)

## Evaluation

### Results (Test Set Performance)

Evaluation metrics calculated against reference summaries across the test set:

## Results

| Model / Baseline            | ROUGE-1 (%) | ROUGE-2 (%) | ROUGE-L (%) |
| --------------------------- | ----------- | ----------- | ----------- |
| **Lead-8 Baseline**         | 18.35       | 5.79        | 15.99       |
| **Lead-12 Baseline**        | 21.87       | 7.04        | 18.21       |
| **Lead-20 Baseline**        | 23.93       | 8.07        | 18.86       |
| **mT5 + LoRA (This Model)** | **25.47**   | **9.27**    | **21.00**   |

## Technical Specifications

### Hardware & Infrastructure

- **Platform:** Kaggle Notebooks
- **GPU:** NVIDIA Tesla T4 / P100 (16GB VRAM)
- **Framework versions:** `transformers`, `peft 0.19.1`, `torchao 0.18.0`

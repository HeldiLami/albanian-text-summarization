import torch
from peft import PeftModel
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

adapter_path = "models/mt5-shqip-LoRA"
base_model_name = "google/mt5-small"

device = "cuda" if torch.cuda.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained(base_model_name)
base_model = AutoModelForSeq2SeqLM.from_pretrained(base_model_name)

model = PeftModel.from_pretrained(base_model, adapter_path)
model = model.merge_and_unload()
model.to(device).eval()

text = input("Insert text u want to summarize:\n")

inputs = tokenizer(
    text,
    max_length=640,
    truncation=True,
    return_tensors="pt",
).to(device)

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

summary = tokenizer.decode(output[0], skip_special_tokens=True)

print("\nSummary:")
print(summary)

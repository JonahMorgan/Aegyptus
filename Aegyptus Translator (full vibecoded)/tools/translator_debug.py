import json
from pathlib import Path
from datasets import Dataset
from transformers import PreTrainedTokenizerFast, AutoModelForSeq2SeqLM, DataCollatorForSeq2Seq, Seq2SeqTrainer, Seq2SeqTrainingArguments
import torch

print('Working dir:', Path('.').resolve())

# paths
here = Path(__file__).resolve().parent
tokenizer_dir = here.parent / 'tokenizer'
corpus_file = here.parent / 'data' / 'train.aegyptus'
base_model = 'Helsinki-NLP/opus-mt-en-de'

# load tokenizer
tokenizer = PreTrainedTokenizerFast.from_pretrained(tokenizer_dir)
print('Loaded tokenizer len:', len(tokenizer))

# load and prepare small dataset
entries = []
with open(corpus_file, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 8:
            break
        entries.append(json.loads(line))

print('Loaded', len(entries), 'entries')

source_max_length = 256
target_max_length = 128

def preprocess(entry):
    source_text = (
        f"[HIERO] {entry.get('hieroglyphs','')}\n"
        f"[TRANS] {entry.get('transliteration','')}\n"
        f"[LEMMA] {entry.get('lemmatization','')}\n"
        f"[GLOSS] {entry.get('glossing','')}"
    )
    target_text = entry.get('translation','') or ''
    model_inputs = tokenizer(source_text, max_length=source_max_length, truncation=True, padding='max_length')
    labels = tokenizer(target_text, max_length=target_max_length, truncation=True, padding='max_length')
    model_inputs['labels'] = labels['input_ids']
    return model_inputs

mapped = [preprocess(e) for e in entries]
print('First mapped example input_ids max id:', max(mapped[0]['input_ids']))

# load model but avoid full network download if possible; we'll only instantiate the config and embeddings
try:
    model = AutoModelForSeq2SeqLM.from_pretrained(base_model)
    print('Model loaded')
except Exception as e:
    print('Model load failed (network?)', e)
    raise

print('Embedding size before resize:', model.get_input_embeddings().weight.shape[0])
model.resize_token_embeddings(len(tokenizer))
print('Embedding size after resize:', model.get_input_embeddings().weight.shape[0])

# prepare dataloader via data collator
data_collator = DataCollatorForSeq2Seq(tokenizer, model=model, padding=True)

# build a tiny trainer to get dataloader
training_args = Seq2SeqTrainingArguments(output_dir='./tmp', per_device_train_batch_size=2, per_device_eval_batch_size=2, num_train_epochs=1)
trainer = Seq2SeqTrainer(model=model, args=training_args, train_dataset=Dataset.from_list(mapped), data_collator=data_collator)

dl = trainer.get_train_dataloader()
for batch in dl:
    print('\nBATCH KEYS:', batch.keys())
    input_ids = batch['input_ids']
    labels = batch['labels']
    print('input_ids shape', input_ids.shape, 'labels shape', labels.shape)
    print('input_ids max', input_ids.max().item(), 'labels max', labels.max().item())
    # check for ids >= embedding size
    emb_size = model.get_input_embeddings().weight.shape[0]
    print('embedding size', emb_size)
    if input_ids.max().item() >= emb_size:
        print('ERROR: input_ids contain ids >= embedding size')
    if labels.max().item() >= emb_size:
        print('ERROR: labels contain ids >= embedding size')
    print('Sample input_ids row:', input_ids[0][:30].tolist())
    print('Sample labels row:', labels[0][:30].tolist())
    break

print('Done')

import json
from pathlib import Path
from datasets import Dataset
from transformers import (
    PreTrainedTokenizerFast,
    AutoModelForSeq2SeqLM,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer,
    DataCollatorForSeq2Seq
)
import torch
import traceback

here = Path(__file__).resolve().parent
tokenizer_dir = here.parent / 'tokenizer'
corpus_file = here.parent / 'data' / 'train.aegyptus'

print('Loading tokenizer from', tokenizer_dir)
tokenizer = PreTrainedTokenizerFast.from_pretrained(tokenizer_dir)
print('Tokenizer len', len(tokenizer))

# load entries
entries = []
with open(corpus_file, 'r', encoding='utf-8') as f:
    for line in f:
        entries.append(json.loads(line))
print('Total entries', len(entries))

# simple split
train_entries = entries[:int(len(entries)*0.9)]
val_entries = entries[int(len(entries)*0.9):]

source_max_length = 256
target_max_length = 128

def preprocess(entry):
    source_text = (
        f"[HIERO] {entry.get('hieroglyphs','')}\n"
        f"[TRANS] {entry.get('transliteration','')}\n"
        f"[LEMMA] {entry.get('lemmatization','')}\n"
        f"[GLOSS] {entry.get('glossing','')}"
    )
    target_text = entry.get('translation', '')
    model_inputs = tokenizer(source_text, max_length=source_max_length, truncation=True, padding='max_length')
    labels = tokenizer(target_text, max_length=target_max_length, truncation=True, padding='max_length')
    # mask label padding ids with -100 so loss ignores them
    pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 0
    label_ids = [ (tid if tid != pad_id else -100) for tid in labels['input_ids'] ]
    model_inputs['labels'] = label_ids
    return model_inputs

train_dataset = Dataset.from_list(train_entries).map(preprocess)
val_dataset = Dataset.from_list(val_entries).map(preprocess)
print('Train/Val sizes', len(train_dataset), len(val_dataset))

print('Loading model...')
base_model = 'Helsinki-NLP/opus-mt-en-de'
model = AutoModelForSeq2SeqLM.from_pretrained(base_model)
try:
    emb_before = model.get_input_embeddings().weight.shape[0]
except Exception:
    emb_before = None
print('model.get_input_embeddings() vocab before resize:', emb_before)
model.resize_token_embeddings(len(tokenizer))
try:
    emb_after = model.get_input_embeddings().weight.shape[0]
except Exception:
    emb_after = None
print('model.get_input_embeddings() vocab after resize:', emb_after)

# print encoder/decoder embedding sizes if available
enc_emb = None
dec_emb = None
try:
    if hasattr(model, 'model') and hasattr(model.model, 'encoder') and hasattr(model.model.encoder, 'embed_tokens'):
        enc_emb = model.model.encoder.embed_tokens.weight.shape[0]
    if hasattr(model, 'model') and hasattr(model.model, 'decoder') and hasattr(model.model.decoder, 'embed_tokens'):
        dec_emb = model.model.decoder.embed_tokens.weight.shape[0]
except Exception:
    pass
print('encoder embed vocab size:', enc_emb, 'decoder embed vocab size:', dec_emb)

# quick static scan: find max token id in datasets
print('\nScanning token ids in train/val for max id (tokenizer only, no model)')
max_id_train = -1
max_id_val = -1
for i, ex in enumerate(train_dataset):
    try:
        m = max(ex['input_ids']) if ex['input_ids'] else -1
        ml = max(ex['labels']) if ex['labels'] else -1
        max_id_train = max(max_id_train, m, ml)
    except Exception:
        pass
for i, ex in enumerate(val_dataset):
    try:
        m = max(ex['input_ids']) if ex['input_ids'] else -1
        ml = max(ex['labels']) if ex['labels'] else -1
        max_id_val = max(max_id_val, m, ml)
    except Exception:
        pass
print('max token id in train examples:', max_id_train)
print('max token id in val examples:  ', max_id_val)

if emb_after is not None:
    if max_id_train >= emb_after or max_id_val >= emb_after:
        print('\nWARNING: Some token ids are >= model embedding size after resize. Listing first problematic examples...')
        bad = []
        for i, ex in enumerate(train_dataset):
            max_id = max(ex['input_ids']) if ex['input_ids'] else -1
            max_lbl = max(ex['labels']) if ex['labels'] else -1
            if max_id >= emb_after or max_lbl >= emb_after:
                bad.append((i, max_id, max_lbl))
                if len(bad) >= 20:
                    break
        print('Found', len(bad), 'problematic train examples (showing up to 20):')
        for b in bad:
            print(b)

# data collator
data_collator = DataCollatorForSeq2Seq(tokenizer, model=model, padding=True, label_pad_token_id=-100)

training_args = Seq2SeqTrainingArguments(output_dir='./models/egyptian_mt', per_device_train_batch_size=4, per_device_eval_batch_size=4, num_train_epochs=1)
trainer = Seq2SeqTrainer(model=model, args=training_args, train_dataset=train_dataset, eval_dataset=val_dataset, tokenizer=tokenizer, data_collator=data_collator)

# inspect a batch before training
dl = trainer.get_train_dataloader()
print('Inspecting a batch from trainer dataloader...')
for batch in dl:
    try:
        print('Batch keys:', batch.keys())
        print('input_ids max', batch['input_ids'].max().item())
        print('labels max', batch['labels'].max().item())
        print('embedding size', model.get_input_embeddings().weight.shape[0])
        break
    except Exception as e:
        print('Error inspecting batch', e)
        traceback.print_exc()
        break

print('Starting trainer.train() (wrapped to catch IndexError)')
try:
    trainer.train()
except Exception as e:
    print('TRAINING ERROR:', type(e), e)
    traceback.print_exc()
    # additional diagnostics: scan all token ids in train dataset for ids >= embedding size
    emb_size = model.get_input_embeddings().weight.shape[0]
    print('\nScanning train dataset for token ids >= embedding size', emb_size)
    bad = []
    for i, ex in enumerate(train_dataset):
        max_id = max(ex['input_ids']) if ex['input_ids'] else -1
        max_lbl = max(ex['labels']) if ex['labels'] else -1
        if max_id >= emb_size or max_lbl >= emb_size:
            bad.append((i, max_id, max_lbl))
            if len(bad) >= 20:
                break
    print('Found', len(bad), 'problematic examples (showing up to 20):')
    for b in bad:
        print(b)

print('Debug script finished')

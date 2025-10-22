from pathlib import Path
import json
import sys
from transformers import PreTrainedTokenizerFast, AutoModelForSeq2SeqLM

print('Working dir:', Path('.').resolve())

tokenizer_dir = Path('./tokenizer')
corpus_file = Path('./data/train.aegyptus')
base_model = 'Helsinki-NLP/opus-mt-en-de'

# Load tokenizer
print('\nLoading tokenizer from', tokenizer_dir)
try:
    tokenizer = PreTrainedTokenizerFast.from_pretrained(tokenizer_dir)
except Exception as e:
    print('Failed to load tokenizer:', e)
    sys.exit(1)

print('len(tokenizer):', len(tokenizer))
print('tokenizer.vocab_size (if present):', getattr(tokenizer, 'vocab_size', None))
try:
    vocab = tokenizer.get_vocab()
    max_vocab_id = max(vocab.values())
    print('max id in tokenizer.get_vocab():', max_vocab_id)
except Exception as e:
    print('Could not get tokenizer vocab mapping:', e)
    vocab = {}

# show special and added tokens
print('special_tokens_map:', getattr(tokenizer, 'special_tokens_map', {}))
added = getattr(tokenizer, 'added_tokens_encoder', {})
print('added_tokens_encoder count:', len(added) if added else 0)
if added:
    # show some added tokens and their ids
    print('some added tokens:', dict(list(added.items())[:20]))

# Load model
print('\nLoading model', base_model)
try:
    model = AutoModelForSeq2SeqLM.from_pretrained(base_model)
except Exception as e:
    print('Failed to load model:', e)
    sys.exit(1)

# find embedding size
def get_embedding_vocab_size(m):
    try:
        emb = m.get_input_embeddings()
        return emb.weight.shape[0]
    except Exception:
        return None

embed_size_before = get_embedding_vocab_size(model)
print('model input embeddings vocab size (before resize):', embed_size_before)

# Tokenize a few examples and check ids
print('\nScanning first 10 entries and their token ids...')
if not corpus_file.exists():
    print('Corpus file not found:', corpus_file)
    sys.exit(1)

bad_ids_found = False
with open(corpus_file, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 10:
            break
        entry = json.loads(line)
        source_text = (
            f"[HIERO] {entry.get('hieroglyphs','')}\n"
            f"[TRANS] {entry.get('transliteration','')}\n"
            f"[LEMMA] {entry.get('lemmatization','')}\n"
            f"[GLOSS] {entry.get('glossing','')}"
        )
        target_text = entry.get('translation','') or ''
        toks_src = tokenizer(source_text, truncation=True, padding=False)
        toks_tgt = tokenizer(target_text, truncation=True, padding=False)
        max_src = max(toks_src['input_ids']) if toks_src['input_ids'] else -1
        max_tgt = max(toks_tgt['input_ids']) if toks_tgt['input_ids'] else -1
        print(f'Entry {i}: max_src_id={max_src}, max_tgt_id={max_tgt}, len_src={len(toks_src["input_ids"])}, len_tgt={len(toks_tgt["input_ids"]) }')
        # check against embed_size_before
        if embed_size_before is not None and (max_src >= embed_size_before or max_tgt >= embed_size_before):
            print('  -> WARNING: token id >= model embedding size before resize')
            bad_ids_found = True

print('\nCalling model.resize_token_embeddings(len(tokenizer)) to match tokenizer size...')
try:
    model.resize_token_embeddings(len(tokenizer))
except Exception as e:
    print('Failed to resize embeddings:', e)

embed_size_after = get_embedding_vocab_size(model)
print('model input embeddings vocab size (after resize):', embed_size_after)

# Re-check token ids against new embedding size
if embed_size_after is not None:
    with open(corpus_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 10:
                break
            entry = json.loads(line)
            source_text = (
                f"[HIERO] {entry.get('hieroglyphs','')}\n"
                f"[TRANS] {entry.get('transliteration','')}\n"
                f"[LEMMA] {entry.get('lemmatization','')}\n"
                f"[GLOSS] {entry.get('glossing','')}"
            )
            target_text = entry.get('translation','') or ''
            toks_src = tokenizer(source_text, truncation=True, padding=False)
            toks_tgt = tokenizer(target_text, truncation=True, padding=False)
            max_src = max(toks_src['input_ids']) if toks_src['input_ids'] else -1
            max_tgt = max(toks_tgt['input_ids']) if toks_tgt['input_ids'] else -1
            if max_src >= embed_size_after or max_tgt >= embed_size_after:
                print(f'Entry {i} STILL has token id >= embedding size after resize: max_src={max_src}, max_tgt={max_tgt}')
                bad_ids_found = True

print('\nSummary: bad_ids_found=', bad_ids_found)
if bad_ids_found:
    print('Some token ids exceed model embeddings. Possible causes: tokenizer has token ids that do not start at 0 or have very large assigned ids, or model resizing failed.\n')
    print('Suggested fixes:')
    print(' - Ensure tokenizer uses small, dense id space (e.g., rebuild tokenizer or remap added tokens to new ids).')
    print(' - Check tokenizer.added_tokens_encoder and special token ids. If any ids are >= embedding size, consider re-saving tokenizer after adding tokens so they get proper ids.')
else:
    print('No token id issues detected for the first 10 entries.')

print('\nDone.')

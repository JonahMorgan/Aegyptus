import json
import torch
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
from hieroglyph_tokenizer import HieroglyphTokenizer
from grammar_transformer import GrammarAwareTransformer
from tokenizers import ByteLevelBPETokenizer

# ----------------------------
# Load tokenizers
# ----------------------------
hiero_tokenizer = HieroglyphTokenizer("data/lexicon_final.json")
german_tokenizer = ByteLevelBPETokenizer(
    "data/tokenizer_german/vocab.json",
    "data/tokenizer_german/merges.txt"
)
german_vocab_size = german_tokenizer.get_vocab_size()

# ----------------------------
# Dataset class
# ----------------------------
class AegyptusDataset(Dataset):
    def __init__(self, jsonl_path):
        self.data = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                self.data.append(json.loads(line))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        print(item)
        hiero_sentence = item["input_text"]
        german_sentence = item["output_text"]

        # --- source ---
        tokens = hiero_tokenizer.tokenize_hieroglyphs(hiero_sentence)
        src_tokens = [hiero_tokenizer.token_to_id.get(t["token"], 0) for t in tokens]
        src_pos = [hiero_tokenizer.pos_to_id.get(t["upos"], 0) for t in tokens]

        # --- target ---
        tgt_tokens = german_tokenizer.encode(german_sentence).ids

        # Teacher forcing: decoder input is tgt_tokens[:-1], output is tgt_tokens[1:]
        tgt_input = tgt_tokens[:-1]
        tgt_output = tgt_tokens[1:]

        return torch.tensor(src_tokens), torch.tensor(src_pos), torch.tensor(tgt_input), torch.tensor(tgt_output)

# ----------------------------
# Collate function for padding
# ----------------------------
def collate_fn(batch):
    src_tokens, src_pos, tgt_input, tgt_output = zip(*batch)
    src_tokens = torch.nn.utils.rnn.pad_sequence(src_tokens, batch_first=True, padding_value=0)
    src_pos = torch.nn.utils.rnn.pad_sequence(src_pos, batch_first=True, padding_value=0)
    tgt_input = torch.nn.utils.rnn.pad_sequence(tgt_input, batch_first=True, padding_value=0)
    tgt_output = torch.nn.utils.rnn.pad_sequence(tgt_output, batch_first=True, padding_value=-100)  # ignore index
    return src_tokens, src_pos, tgt_input, tgt_output

# ----------------------------
# DataLoader
# ----------------------------
dataset = AegyptusDataset("dataset_word_subword_hg2de.jsonl")
train_loader = DataLoader(dataset, batch_size=8, shuffle=True, collate_fn=collate_fn)

# ----------------------------
# Model
# ----------------------------
model = GrammarAwareTransformer(
    vocab_size=german_vocab_size,
    pos_size=len(hiero_tokenizer.pos_to_id)+1,
    nhead=8,
    dim_feedforward=512,
    dropout=0.1
)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# ----------------------------
# Optimizer & loss
# ----------------------------
optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
criterion = torch.nn.CrossEntropyLoss(ignore_index=-100)

# ----------------------------
# Training loop
# ----------------------------
epochs = 10
for epoch in range(epochs):
    model.train()
    pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}")
    total_loss = 0.0

    for src_tokens, src_pos, tgt_input, tgt_output in pbar:
        src_tokens = src_tokens.to(device)
        src_pos = src_pos.to(device)
        tgt_input = tgt_input.to(device)
        tgt_output = tgt_output.to(device)

        optimizer.zero_grad()
        logits = model(src_tokens, src_pos, tgt_input)  # shape: [B, T, vocab_size]

        # reshape for CE loss
        logits_flat = logits.view(-1, logits.size(-1))
        tgt_output_flat = tgt_output.view(-1)

        loss = criterion(logits_flat, tgt_output_flat)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        pbar.set_postfix({"loss": total_loss / (pbar.n + 1)})

    print(f"Epoch {epoch+1} average loss: {total_loss / len(train_loader):.4f}")

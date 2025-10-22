# train_grammar_transformer.py
import json
from tqdm import tqdm
import torch
from torch.utils.data import Dataset, DataLoader
from torch import nn
import torch.nn.functional as F
from hieroglyph_tokenizer import HieroglyphTokenizer
from tokenizers import Tokenizer

# ----------------------------
# Dataset
# ----------------------------
class Seq2SeqDataset(Dataset):
    def __init__(self, jsonl_path, src_tokenizer, tgt_tokenizer, max_src_len=50, max_tgt_len=128):
        self.samples = []
        self.src_tokenizer = src_tokenizer
        self.tgt_tokenizer = tgt_tokenizer
        self.max_src_len = max_src_len
        self.max_tgt_len = max_tgt_len

        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                self.samples.append(data)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        src_tokens = self.src_tokenizer.tokenize_transliteration(sample["input_text"])
        src_ids = [self.src_tokenizer.vocab.get(t['token'], 0) for t in src_tokens]
        src_ids = src_ids[:self.max_src_len]

        tgt_enc = self.tgt_tokenizer.encode(sample["output_text"])
        tgt_ids = tgt_enc.ids[:self.max_tgt_len]

        return torch.tensor(src_ids, dtype=torch.long), torch.tensor(tgt_ids, dtype=torch.long)

# ----------------------------
# Collate function
# ----------------------------
def collate_fn(batch):
    src_batch, tgt_batch = zip(*batch)
    src_lens = [len(s) for s in src_batch]
    tgt_lens = [len(t) for t in tgt_batch]

    max_src_len = max(src_lens)
    max_tgt_len = max(tgt_lens)

    src_padded = torch.zeros(len(batch), max_src_len, dtype=torch.long)
    tgt_padded = torch.zeros(len(batch), max_tgt_len, dtype=torch.long)

    for i, (s, t) in enumerate(zip(src_batch, tgt_batch)):
        src_padded[i, :len(s)] = s
        tgt_padded[i, :len(t)] = t

    return src_padded, tgt_padded

# ----------------------------
# Grammar-aware Transformer
# ----------------------------
import torch
import torch.nn as nn
import torch.nn.functional as F

class GrammarAwareTransformer(nn.Module):
    def __init__(
        self,
        vocab_size: int,
        pos_size: int,
        d_model: int = 512,
        nhead: int = 8,
        num_layers: int = 6,
        dim_feedforward: int = 2048,
        dropout: float = 0.1,
        max_len: int = 512
    ):
        super().__init__()

        # Token and POS embeddings
        self.token_embedding = nn.Embedding(vocab_size, d_model)
        self.pos_embedding = nn.Embedding(pos_size + 1, d_model)  # +1 for unknown/pad

        # Positional embeddings
        self.positional_embedding = nn.Embedding(max_len, d_model)

        # Transformer
        self.transformer = nn.Transformer(
            d_model=d_model,
            nhead=nhead,
            num_encoder_layers=num_layers,
            num_decoder_layers=num_layers,
            dim_feedforward=dim_feedforward,
            dropout=dropout
        )

        # Final projection
        self.fc_out = nn.Linear(d_model, vocab_size)

        self.d_model = d_model
        self.max_len = max_len

    def forward(self, src_tokens, src_pos, tgt_tokens):
        """
        src_tokens: [seq_len_src, batch]
        src_pos:    [seq_len_src, batch] (POS indices)
        tgt_tokens: [seq_len_tgt, batch]
        """

        seq_len_src, batch_size = src_tokens.size()
        seq_len_tgt = tgt_tokens.size(0)

        # Encoder embeddings: token + POS + positional
        src_token_emb = self.token_embedding(src_tokens)
        src_pos_emb = self.pos_embedding(src_pos)
        positions_src = torch.arange(seq_len_src, device=src_tokens.device).unsqueeze(1).expand(seq_len_src, batch_size)
        src_positional_emb = self.positional_embedding(positions_src)
        src_emb = src_token_emb + src_pos_emb + src_positional_emb

        # Decoder embeddings
        tgt_emb = self.token_embedding(tgt_tokens)
        positions_tgt = torch.arange(seq_len_tgt, device=tgt_tokens.device).unsqueeze(1).expand(seq_len_tgt, batch_size)
        tgt_positional_emb = self.positional_embedding(positions_tgt)
        tgt_emb = tgt_emb + tgt_positional_emb  # decoder doesn’t use POS embeddings

        # Causal mask for decoder
        tgt_mask = self.transformer.generate_square_subsequent_mask(seq_len_tgt).to(tgt_tokens.device)

        # Forward through transformer
        memory = self.transformer.encoder(src_emb)
        output = self.transformer.decoder(tgt_emb, memory, tgt_mask=tgt_mask)

        # Project to vocab
        logits = self.fc_out(output)  # [seq_len_tgt, batch, vocab_size]

        return logits

# ----------------------------
# Training loop
# ----------------------------
def train(model, dataloader, epochs=10, lr=1e-4, device='cuda'):
    model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss(ignore_index=0)

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        pbar = tqdm(dataloader, desc=f"Epoch {epoch+1}/{epochs}")
        for src, tgt in pbar:
            src, tgt = src.to(device), tgt.to(device)
            tgt_input = tgt[:, :-1]
            tgt_output = tgt[:, 1:]

            optimizer.zero_grad()
            logits = model(src, tgt_input)

            loss = criterion(logits.reshape(-1, logits.size(-1)), tgt_output.reshape(-1))
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            pbar.set_postfix({'loss': total_loss / (pbar.n + 1)})

# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":
    # Source tokenizer
    src_tokenizer = HieroglyphTokenizer("data/lexicon_final.json")
    # build vocab from dataset
    tokens = set()
    with open("dataset_word_subword_hg2de.jsonl", "r") as f:
        for line in f:
            data = json.loads(line)
            toks = src_tokenizer.tokenize_transliteration(data["input_text"])
            for t in toks:
                tokens.add(t['token'])
    src_tokenizer.vocab = {tok: i+1 for i, tok in enumerate(sorted(tokens))}
    src_tokenizer.vocab["<UNK>"] = 0

    # Target tokenizer
    tgt_tokenizer = Tokenizer.from_file("german-bpe.json")

    dataset = Seq2SeqDataset("dataset_word_subword_hg2de.jsonl", src_tokenizer, tgt_tokenizer)
    dataloader = DataLoader(dataset, batch_size=8, shuffle=True, collate_fn=collate_fn)

    model = GrammarAwareTransformer(
        src_vocab_size=len(src_tokenizer.vocab),
        tgt_vocab_size=tgt_tokenizer.get_vocab_size()
    )

    train(model, dataloader, epochs=10, device='cuda')

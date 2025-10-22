# hieroglyph_tokenizer_combined_with_pos.py
import json
import re
from typing import List, Dict, Any

class HieroglyphTokenizer:
    def __init__(self, lexicon_path: str):
        with open(lexicon_path, "r", encoding="utf-8") as f:
            self.lexicon = json.load(f)

        # ----------------------------
        # Build POS mappings
        # ----------------------------
        pos_set = set()
        for entry in self.lexicon.values():
            upos = entry.get("upos")
            if isinstance(upos, list):
                pos_set.update(upos)
            elif upos:
                pos_set.add(upos)

        # Mapping from POS tag to integer ID (0 reserved for padding/unknown)
        self.pos_to_id = {pos: i + 1 for i, pos in enumerate(sorted(pos_set))}
        self.id_to_pos = {i: pos for pos, i in self.pos_to_id.items()}

    # ----------------------------
    # Subword splitting helpers
    # ----------------------------
    def _tokenize_subwords(self, word_translit: str, lemma_translit: str):
        prefixes, suffixes = [], []
        temp = word_translit

        # Leading prefixes like (x)
        while True:
            m = re.match(r"^\([^\)]+\)", temp)
            if not m: break
            candidate = m.group(0)
            if not lemma_translit.startswith(candidate):
                prefixes.append(candidate)
                temp = temp[len(candidate):]
            else:
                break

        # Trailing suffixes like .x or =x
        while True:
            m = re.search(r"(\.|=)[^\s\.=]+$", temp)
            if not m: break
            candidate = m.group(0)
            if not lemma_translit.endswith(candidate):
                suffixes.insert(0, candidate)
                temp = temp[:-len(candidate)]
            else:
                break

        root = temp
        return prefixes, root, suffixes

    # ----------------------------
    # Build token dict
    # ----------------------------
    def _build_token_dict(self, token_str: str, token_type: str,
                          upos: Any, lemma: str, gloss: str, gardiner: Any) -> Dict[str, Any]:
        upos_str = upos[0] if isinstance(upos, list) and upos else upos
        tag = token_type.upper()
        if tag == "PREFIX":
            tag = f"PRE {upos_str.upper()}" if upos_str else "PRE"
        elif tag == "SUFFIX":
            tag = f"SUF {upos_str.upper()}" if upos_str else "SUF"
        elif tag == "ROOT":
            tag = upos_str.upper() if upos_str else "ROOT"
        elif tag == "UNKNOWN":
            tag = "UNKNOWN"

        return {
            "token": token_str,
            "type": tag,
            "lemma": lemma,
            "upos": upos_str,
            "upos_id": self.pos_to_id.get(upos_str, 0) if upos_str else 0,
            "gloss": gloss,
            "gardiner": gardiner
        }

    # ----------------------------
    # Tokenize a single word variant
    # ----------------------------
    def _tokenize_word_by_variant(self, variant: Dict[str, Any], lemma_translit: str, upos: Any) -> List[Dict[str, Any]]:
        word_translit = variant.get("translit", "")
        gloss = variant.get("gloss", None)
        gardiner = variant.get("gardiner", None)
        prefixes, root, suffixes = self._tokenize_subwords(word_translit, lemma_translit)

        tokens = []
        for p in prefixes:
            tokens.append(self._build_token_dict(p, "PREFIX", upos, lemma_translit, gloss, None))
        tokens.append(self._build_token_dict(root, "ROOT", upos, lemma_translit, gloss, gardiner))
        for s in suffixes:
            tokens.append(self._build_token_dict(s, "SUFFIX", upos, lemma_translit, gloss, None))
        return tokens

    # ----------------------------
    # Per-glyph fallback for unknown words
    # ----------------------------
    def _tokenize_per_glyph(self, glyph_word: str) -> List[Dict[str, Any]]:
        translit_parts = []
        for g in glyph_word:
            found = False
            for lemma_id, entry in self.lexicon.items():
                for var in entry.get("glyph_variants", []):
                    if g == var.get("glyph"):
                        translit_parts.append(var.get("translit"))
                        found = True
                        break
                if found: break
            if not found:
                translit_parts.append("?")  # unknown glyph fallback
        return [{
            "token": "".join(translit_parts),
            "type": "UNKNOWN",
            "lemma": None,
            "upos": None,
            "upos_id": 0,
            "gloss": None,
            "gardiner": None
        }]

    # ----------------------------
    # Tokenize hieroglyphic word
    # ----------------------------
    def _tokenize_word_from_glyph(self, glyph_word: str) -> List[Dict[str, Any]]:
        glyph_word = glyph_word.strip()
        for lemma_id, entry in self.lexicon.items():
            for var in entry.get("glyph_variants", []):
                glyph_str = var.get("glyph") if isinstance(var.get("glyph"), str) else "".join(var.get("glyph"))
                if glyph_word == glyph_str:
                    return self._tokenize_word_by_variant(var, entry.get("lemma", ""), entry.get("upos"))

        # fallback
        return self._tokenize_per_glyph(glyph_word)

    # ----------------------------
    # Hieroglyphic sentence tokenization
    # ----------------------------
    def tokenize_hieroglyphs(self, sentence: str) -> List[Dict[str, Any]]:
        all_tokens = []
        for w in sentence.strip().split():
            all_tokens.extend(self._tokenize_word_from_glyph(w))
        return all_tokens

    # ----------------------------
    # Transliteration sentence tokenization
    # ----------------------------
    def tokenize_transliteration(self, sentence: str) -> List[Dict[str, Any]]:
        all_tokens = []
        for word in sentence.strip().split():
            lemma_id, variant, entry_upos = None, None, None
            for k, v in self.lexicon.items():
                for var in v.get("glyph_variants", []):
                    if word == var.get("translit") or word.startswith(var.get("translit", "")) or word.endswith(var.get("translit", "")):
                        lemma_id, variant, entry_upos = k, var, v.get("upos")
                        break
                if lemma_id: break

            if lemma_id:
                lemma_translit = self.lexicon[lemma_id]["lemma"]
                upos = entry_upos
                gloss = variant.get("gloss") if variant else None
                gardiner = variant.get("gardiner") if variant else None
                prefixes, root, suffixes = self._tokenize_subwords(word, lemma_translit)
                for p in prefixes:
                    all_tokens.append(self._build_token_dict(p, "PREFIX", upos, lemma_translit, gloss, None))
                all_tokens.append(self._build_token_dict(root, "ROOT", upos, lemma_translit, gloss, gardiner))
                for s in suffixes:
                    all_tokens.append(self._build_token_dict(s, "SUFFIX", upos, lemma_translit, gloss, None))
            else:
                # unknown word
                all_tokens.append(self._build_token_dict(word, "UNKNOWN", None, None, None, None))
        return all_tokens

    # ----------------------------
    # Convert tokens to model-ready string
    # ----------------------------
    def tokens_to_string(self, tokens: List[Dict[str, Any]]) -> str:
        return " ".join(f"[{t['type']}]{t['token']}" for t in tokens)


# ----------------------------
# Example usage
# ----------------------------
if __name__ == "__main__":
    tokenizer = HieroglyphTokenizer("data/lexicon_final.json")

    hiero_sent = "𓅱𓂧𓎡𓄿 𓂓𓏏𓈖"
    tokens_hiero = tokenizer.tokenize_hieroglyphs(hiero_sent)
    print("=== Hieroglyphic input ===")
    for t in tokens_hiero:
        print(t)
    print("Model input string:", tokenizer.tokens_to_string(tokens_hiero))

    translit_sent = "wdi̯.kꜣ kt.t"
    tokens_translit = tokenizer.tokenize_transliteration(translit_sent)
    print("\n=== Transliteration input ===")
    for t in tokens_translit:
        print(t)
    print("Model input string:", tokenizer.tokens_to_string(tokens_translit))

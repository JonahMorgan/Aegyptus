# hieroglyph_parser_training.py
import json
import re
from typing import List, Dict

class HieroglyphParser:
    def __init__(self, lexicon_path: str):
        with open(lexicon_path, "r", encoding="utf-8") as f:
            self.lexicon = json.load(f)
        self.sorted_signs = sorted(self.lexicon.keys(), key=len, reverse=True)

    # -------------------------
    # Morphological helpers
    # -------------------------
    @staticmethod
    def is_prefix(translit: str) -> bool:
        return bool(re.fullmatch(r"\([a-zA-Z]+\)", translit))

    @staticmethod
    def is_suffix(translit: str) -> bool:
        return bool(re.fullmatch(r"(\.|=)[a-zA-Z]+", translit))

    @staticmethod
    def is_determinative(translit: str) -> bool:
        return translit in ["", "-"]

    @staticmethod
    def add_morph_marker(translit: str) -> str:
        if HieroglyphParser.is_prefix(translit):
            return f"{translit}[prefix]"
        elif HieroglyphParser.is_suffix(translit):
            return f"{translit}[suffix]"
        elif HieroglyphParser.is_determinative(translit):
            return f"{translit}[det]"
        return translit

    # -------------------------
    # Core parsing
    # -------------------------
    def parse_word(self, word: str) -> List[Dict]:
        tokens = []
        t = word.strip()
        while t:
            match = None
            for sign in self.sorted_signs:
                if t.startswith(sign):
                    match = sign
                    entry = self.lexicon[sign]
                    translit = entry.get("transliterations", [""])[0]
                    upos = entry.get("upos", ["unknown"])[0]
                    lemma = entry.get("lemmas", [""])[0]
                    gloss = entry.get("glosses", [""])[0]
                    translit_marked = self.add_morph_marker(translit)

                    tokens.append({
                        "glyph": sign,
                        "gardiner": entry.get("gardiner", [[]])[0],
                        "type": upos,
                        "upos": upos,
                        "lemma": lemma,
                        "gloss": gloss,
                        "translit": translit_marked,
                        "prefix": self.is_prefix(translit),
                        "suffix": self.is_suffix(translit),
                        "determinative": self.is_determinative(translit)
                    })
                    t = t[len(sign):].strip()
                    break
            if not match:
                tokens.append({
                    "glyph": t[0],
                    "gardiner": [f"UNK({t[0]})"],
                    "type": "unknown",
                    "upos": "unknown",
                    "lemma": "",
                    "gloss": "",
                    "translit": "",
                    "prefix": False,
                    "suffix": False,
                    "determinative": False
                })
                t = t[1:]
        return tokens

    def parse_sentence(self, sentence: str) -> List[List[Dict]]:
        words = sentence.strip().split()
        return [self.parse_word(w) for w in words]

    # -------------------------
    # Transliteration
    # -------------------------
    def get_word_transliteration(self, word_tokens: List[Dict]) -> str:
        return " ".join([tok["translit"] for tok in word_tokens if tok["translit"]])

    def get_sentence_transliteration(self, sentence: str) -> str:
        parsed = self.parse_sentence(sentence)
        return " ".join([self.get_word_transliteration(w) for w in parsed])

    # -------------------------
    # Model-friendly tokenization
    # -------------------------
    def tokenize_for_model(self, sentence: str) -> str:
        parsed = self.parse_sentence(sentence)
        out_tokens = []
        for word_tokens in parsed:
            for tok in word_tokens:
                out_tokens.append(f"[{tok['upos'].upper()}] {tok['glyph']} [{tok['lemma']}] [{tok['gloss']}]")
        return " ".join(out_tokens)

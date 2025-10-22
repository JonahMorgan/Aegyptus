# build_lexicon_flat_glyphs.py
import json
import re
import unicodedata
from collections import defaultdict

# ----------------------------
# Helper functions
# ----------------------------

def parse_translit_affixes(translit: str):
    """
    Extract prefixes and suffixes from transliteration without modifying original translit.
    Returns (prefixes, suffixes)
    """
    prefixes = []
    suffixes = []
    temp = translit

    # Extract all leading prefixes
    while True:
        m = re.match(r"^\([^\)]+\)", temp)
        if not m:
            break
        prefixes.append(m.group(0))
        temp = temp[len(m.group(0)):]

    # Extract all trailing suffixes
    while True:
        m = re.search(r"(\.|=)[^\s\.\=]+$", temp)
        if not m:
            break
        suffixes.insert(0, m.group(0))
        temp = temp[:-len(m.group(0))]

    return prefixes, suffixes

def unicode_to_gardiner(cluster: str):
    """Convert one or more Unicode hieroglyphs to Gardiner codes."""
    codes = []
    for c in cluster:
        try:
            name = unicodedata.name(c)
        except ValueError:
            codes.append(f"UNK({c})")
            continue
        if name.startswith("EGYPTIAN HIEROGLYPH"):
            code = name.split(" ")[-1]
            letter = ''.join(filter(str.isalpha, code))
            number = ''.join(filter(str.isdigit, code)).lstrip("0")
            codes.append(f"{letter}{number}")
        else:
            codes.append(f"UNK({c})")
    return codes

import re
import unicodedata

import re
import unicodedata

# Matches things like "A1", "Aa12", "V31Aa", "Z2", etc.
GARDINER_PATTERN = re.compile(r"^[A-Z][0-9]+[A-Za-z]*$")

def glyph_to_gardiner(glyph: str):
    """
    Convert a mixed glyph string (Unicode + possible <g> tags)
    into a flattened list of Gardiner codes.
    Handles embedded <g>…</g> anywhere in the glyph.
    """
    glyph = glyph.strip()
    if not glyph:
        return []

    gardiners = []

    # Replace inline <g>...</g> sections with placeholders
    parts = re.split(r"(<g>.*?</g>)", glyph)

    for part in parts:
        if not part.strip():
            continue
        # Handle Gardiner tags first
        m = re.fullmatch(r"<g>\s*(.+?)\s*</g>", part)
        if m:
            val = m.group(1).strip()
            # Keep known Gardiner codes or placeholders like (unidentified)
            if val:
                gardiners.append(val.upper())
            continue

        # Otherwise, treat as Unicode hieroglyphs
        for c in part:
            try:
                name = unicodedata.name(c)
                if name.startswith("EGYPTIAN HIEROGLYPH"):
                    code = name.split(" ")[-1]
                    letter = ''.join(filter(str.isalpha, code))
                    number = ''.join(filter(str.isdigit, code)).lstrip("0")
                    gardiners.append(f"{letter}{number}")
                else:
                    # skip empty or private use characters
                    if not name.startswith("<") and c.strip():
                        gardiners.append(f"UNK({c})")
            except ValueError:
                if c.strip():
                    gardiners.append(f"UNK({c})")

    # Filter out empty or null UNK()
    gardiners = [g for g in gardiners if g != "UNK()" and g != "UNK(︂)"]

    return gardiners

def _unicode_segment_to_gardiner(segment: str):
    """
    Convert a string of Unicode hieroglyphs to Gardiner codes.
    Unknowns are returned as UNK(<symbol>), ignoring invisible/control marks.
    """
    codes = []
    for c in segment:
        # Treat invisible or control characters as empty
        if c.isspace() or unicodedata.category(c) in ["Mn", "Cf"]:
            continue

        try:
            name = unicodedata.name(c)
        except ValueError:
            codes.append(f"UNK({c})")
            continue

        if name.startswith("EGYPTIAN HIEROGLYPH"):
            code_part = name.split(" ")[-1]
            letter = ''.join(filter(str.isalpha, code_part))
            number = ''.join(filter(str.isdigit, code_part)).lstrip("0")
            codes.append(f"{letter}{number}")
        else:
            codes.append(f"UNK({c})")
    return codes

def split_sentence_preserve_words(sentence: str):
    """
    Split a hieroglyphic sentence into words, preserving:
      - Gardiner placeholders like <g>V31Aa</g> or <g>(UNIDENTIFIED)</g>
      - Bare Gardiner codes (e.g., V31Aa, D36, Aa12)
      - Single Unicode hieroglyphs
    """
    words = sentence.strip().split()
    sentence_words = []
    for word in words:
        clusters = re.findall(
            r"<g>.*?</g>|[A-Z]{1,2}[0-9]{1,3}[A-Za-z]*|.", word
        )
        sentence_words.append(clusters)
    return sentence_words


def sentence_to_gardiner_words(sentence: str):
    """Convert a hieroglyphic sentence into a list of lists of Gardiner codes (flattened)."""
    words_clusters = split_sentence_preserve_words(sentence)
    sentence_gardiner = []
    for word in words_clusters:
        codes = []
        for g in word:
            codes.extend(glyph_to_gardiner(g))  # flatten
        sentence_gardiner.append(codes)
    return sentence_gardiner

# ----------------------------
# Lexicon builder (flatten glyphs)
# ----------------------------

def build_lexicon(jsonl_path: str, output_path: str):
    lexicon = defaultdict(lambda: {
        "lemma": "",
        "upos": "",
        "gloss": "",
        "glyph_variants": [],
        "examples": []
    })

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            hiero_sentence = data["hieroglyphs"].split()
            translit_tokens = data["transliteration"].split()
            upos_tokens = data["UPOS"].split()
            lemmatization_tokens = data.get("lemmatization", "").split()
            gloss_tokens = data.get("glossing", "").split()

            sentence_gardiner = sentence_to_gardiner_words(data["hieroglyphs"])

            for i, lemma_entry in enumerate(lemmatization_tokens):
                if "|" not in lemma_entry:
                    continue
                lemma_id, _ = lemma_entry.split("|")
                glyph = hiero_sentence[i] if i < len(hiero_sentence) else ""
                translit = translit_tokens[i] if i < len(translit_tokens) else ""
                upos = upos_tokens[i] if i < len(upos_tokens) else ""
                gloss = gloss_tokens[i] if i < len(gloss_tokens) else ""

                prefixes, suffixes = parse_translit_affixes(translit)

                gardiner_codes = glyph_to_gardiner(glyph)

                entry = lexicon[lemma_id]
                entry["lemma"] = translit
                entry["upos"] = upos
                entry["gloss"] = gloss

                # Only store single glyph per variant
                variant = {
                    "glyph": glyph,
                    "translit": translit,
                    "prefixes": prefixes,
                    "suffixes": suffixes,
                    "gardiner": gardiner_codes,
                    "gloss": gloss
                }

                if variant not in entry["glyph_variants"]:
                    entry["glyph_variants"].append(variant)

                example = {
                    "sentence_hiero": data["hieroglyphs"],
                    "sentence_translit": data["transliteration"],
                    "sentence_upos": data["UPOS"],
                    "sentence_gloss": data.get("glossing", ""),
                    "sentence_gardiner": sentence_gardiner,
                    "translation": data.get("translation", ""),
                    "dateNotBefore": data.get("dateNotBefore", ""),
                    "dateNotAfter": data.get("dateNotAfter", "")
                }
                entry["examples"].append(example)

    with open(output_path, "w", encoding="utf-8") as out_f:
        json.dump(lexicon, out_f, ensure_ascii=False, indent=2)

    print(f"Lexicon saved to {output_path}")

# ----------------------------
# Example usage
# ----------------------------
if __name__ == "__main__":
    build_lexicon("data/train.aegyptus", "data/lexicon_final.json")

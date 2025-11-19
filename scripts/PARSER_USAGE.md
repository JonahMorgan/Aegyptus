# Bulk Lemma Parser Summary

## Overview
Created `parse_all_lemmas.py` to parse raw HTML data from `all_lemmas.jsonl` into structured JSON format using the same parsing method that produced `c37_final.json`.

## Script Features

### Input
- Reads raw HTML from `all_lemmas.jsonl` (JSONL format)
- Each entry contains: `{"tla": "C1", "html": "...", "fetched_at": "..."}`

### Parsing Method
Uses the proven parsing logic from `scrape_coptic_dictionary.py` - `parse_entry_dom()`:

1. **Lemmas Extraction**
   - Detects Coptic characters (U+2C80–U+2CFF)
   - Reads form, dialect (S/F/B), form ID (CF###), and POS on consecutive lines
   - Ensures no duplicates

2. **Senses Extraction**
   - Bounded by "Scriptorium tag:" and "Descended from" markers
   - Parses numbered sense entries (1., 2., 3., etc.)
   - Extracts translations in English, French, and German

3. **Etymology Extraction**
   - Extracts "Descended from" section
   - Captures Demotic and Hieroglyphic forms
   - Separates main etymology from "cf." (compare) cognates
   - Extracts WCN (World Coptic Numeric) IDs

4. **Examples & References**
   - Extracts example usage with URNs
   - Captures "See also" TLA cross-references

### Output Files

1. **all_lemmas_parsed.jsonl**
   - Newline-delimited JSON format
   - One entry per line
   - Useful for streaming/line-by-line processing

2. **all_lemmas_parsed.json**
   - JSON array format
   - Complete summary of all entries
   - Easy to load in Python/JavaScript

3. **parse_stats.json**
   - Parsing statistics
   - Counts of entries with lemmas, senses, etymology

## Usage

```bash
# Parse with defaults
python parse_all_lemmas.py

# Custom input/output paths
python parse_all_lemmas.py \
  --input raw_data.jsonl \
  --output-jsonl parsed.jsonl \
  --output-json parsed.json \
  --stats stats.json
```

## Test Results (5 Entries)

```
Total entries:      5
Successful:         5
Failed:             0
With lemmas:        2
With senses:        2
With etymology:     2
```

## Example Output Structure

```json
{
  "tla": "C2",
  "title": "TLA lemma no. C2ⲁ-",
  "lemmas": [
    {
      "Form": "ⲁ⸗",
      "Dialect": "S",
      "Form ID": "CF10",
      "POS": "optional"
    }
  ],
  "senses": [
    {
      "sense_id": "1",
      "en": "verbal prefix perfect I",
      "fr": "préfixe verbal parfait I",
      "de": "Präfix Perfekt I"
    }
  ],
  "etymology": {
    "raw": "full etymology text",
    "main": {
      "demotic": "r",
      "hieroglyphic": "NA",
      "description": "optional description"
    },
    "cf": {
      "raw": "cognate section text",
      "terms": [{"term": "ⲁⲛⲍⲏⲃⲉ", "gloss": "school"}]
    },
    "wcn": {"WCNae": ["12345"], "WCNde": ["d999"]}
  },
  "examples": [...],
  "see_also": {"C1": "entry.cgi?tla=C1"},
  "refs": []
}
```

## Next Steps

1. Run bulk fetcher on full range: `python fetch_all_lemmas.py --start C1 --end C9999`
2. Parse all fetched data: `python parse_all_lemmas.py`
3. Further processing as needed (CSV export, database import, etc.)

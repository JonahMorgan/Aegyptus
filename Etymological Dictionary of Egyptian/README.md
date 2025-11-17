# Etymological Dictionary of Egyptian - Parser

This directory contains a parser for extracting lemma entries from the Etymological Dictionary of Egyptian PDF.

## Setup

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Usage

### Test Mode (First 5 Pages)

```powershell
python parse_ede.py --test
```

### Parse Specific Pages

```powershell
python parse_ede.py --start-page 0 --end-page 20 --output sample_lemmas.json
```

### Parse Entire Dictionary

```powershell
python parse_ede.py --output ede_lemmas.json
```

## Output Format

The parser extracts lemmas into JSON format with the following structure:

```json
[
  {
    "headword": "ꜣ",
    "text": "Full lemma text including definitions, etymology, etc.",
    "page": 15,
    "font_info": {
      "font": "TimesNewRomanPS-BoldMT",
      "size": 12.0,
      "flags": 16
    }
  }
]
```

## Features

- **Automatic headword detection**: Uses font styling (bold, size) and Egyptian character presence
- **Full text extraction**: Preserves complete lemma text including etymology and definitions
- **Page tracking**: Records source page for each lemma
- **Clean output**: Removes hyphenation and normalizes whitespace
- **Configurable**: Parse specific page ranges or entire document

## Next Steps

After extracting raw lemma text, you can build additional parsers to:
- Extract structured etymological information
- Parse definitions and meanings
- Extract cross-references
- Parse attestations and citations
- Link to hieroglyphic forms

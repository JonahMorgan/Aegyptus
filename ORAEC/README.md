# ORAEC - Coptic Etymologies Database

## Overview

This folder contains a comprehensive database of **2,177 etymological relationships** between Coptic words and their Egyptian/Demotic predecessors, extracted from the ORAEC (Online Resource for the Ancient Egyptian Corpus) project.

## Contents

### Data Files

1. **`coptic_etymologies_complete.json`** (17,532 lines)
   - Complete database in JSON format
   - Contains all 2,177 etymological entries
   - Includes ID mappings and URLs
   - Sample entries have word forms in original scripts

2. **`coptic_etymologies_complete.jsonl`**
   - Same data in JSON Lines format
   - One entry per line for easier streaming

3. **`statistics.json`**
   - Detailed statistics about coverage and relationships

### Repository Clone

4. **`coptic_etymologies_repo/`**
   - Complete clone of https://github.com/oraec/coptic_etymologies
   - Contains:
     - `digitizing_coptic_etymologies_coptic_list_entries.csv` - Source CSV with all ID mappings
     - `README.md` - Original repository documentation
     - `LICENSE` - CC0 1.0 license

### Scripts

5. **`extract_all_etymologies.py`**
   - Main extraction script
   - Parses CSV and merges with HTML table data
   - Generates JSON/JSONL output files

6. **`enhance_with_table.py`**
   - Enhancement script that fetches the full blog table and adds word forms
   - Uses a network fetch with a local cache fallback (`blog_table_cache.txt`)
   - Outputs `coptic_etymologies_enhanced.json` and `.jsonl`

#### Enhance with full blog table

This script downloads the complete table from the blog post and merges the
word forms into the existing dataset:

1. Ensure the virtual environment is active or use the provided interpreter.
2. Run the enhancement script from the `ORAEC/` folder.

It will:
- Fetch: https://oraec.github.io/2024/08/17/digitization-of-coptic-etymologies.html
- Cache the raw page in `blog_table_cache.txt` for offline runs
- Parse all rows and update entries by `coptic_id`
- Save: `coptic_etymologies_enhanced.json` and `coptic_etymologies_enhanced.jsonl`

#### Diffing enhancements

Use `diff_enhancements.py` to see what changed compared to the original dataset.

Example (PowerShell):
```powershell
python diff_enhancements.py --limit 15 --fields coptic_word,egyptian_word,demotic_word
```
You will see which word-form fields were added or modified.

### Documentation

7. **`README.md`** (this file)
8. **`EXTRACTION_SUMMARY.md`** - Detailed extraction process and results

## Data Structure

Each entry contains:

```json
{
  "coptic_id": "C135",           // Coptic Dictionary Online ID
  "egyptian_id": "27940",        // ORAEC corpus ID
  "demotic_id": "590",           // TLA demotic ID
  "coptic_url": "https://coptic-dictionary.org/entry.cgi?tla=C135",
  "egyptian_url": "https://oraec.github.io/corpus/27940.html",
  "demotic_url": "https://aaew.bbaw.de/tla/servlet/GetWcnDetails?&wn=590&db=1",
  "coptic_word": "ⲁⲛⲟⲕ",          // Coptic script (when available)
  "egyptian_word": "jnk",         // Egyptian transliteration
  "demotic_word": "jnky"          // Demotic transliteration
}
```

## Coverage Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Entries** | 2,177 | 100.0% |
| With Egyptian ID | 1,695 | 77.9% |
| With Demotic ID | 1,827 | 83.9% |
| With Both | 1,345 | 61.8% |
| Egyptian Only | 350 | 16.1% |
| Demotic Only | 482 | 22.1% |

## Example Entries

### 1. Personal Pronoun "I"
- **Coptic**: ⲁⲛⲟⲕ (anok)
- **Egyptian**: jnk (jnk)
- **Demotic**: jnky (jnky)
- Shows consistent pronoun form across all three stages

### 2. Word for "verily, indeed"
- **Coptic**: ⲁⲙⲓⲛ (amin)
- **Egyptian**: mn (men)
- **Demotic**: mn (men)
- Semantic consistency through language evolution

## Research Applications

This database enables:

1. **Historical Linguistics**: Track phonological changes across 3000+ years
2. **Comparative Analysis**: Compare Egyptian → Demotic → Coptic transitions
3. **Digital Humanities**: Build etymological visualization tools
4. **Language Learning**: Help students connect Coptic to earlier forms

## Data Sources

1. **Coptic Dictionary Online**: https://coptic-dictionary.org/
2. **ORAEC**: https://oraec.github.io/
3. **TLA**: https://aaew.bbaw.de/tla/
4. **GitHub Repository**: https://github.com/oraec/coptic_etymologies
5. **Blog Post**: https://oraec.github.io/2024/08/17/digitization-of-coptic-etymologies.html

Note: The enhancement step fetches this page and parses its table directly.

## License

This data is licensed under **CC0 1.0 Universal** (Public Domain Dedication) by the ORAEC project.

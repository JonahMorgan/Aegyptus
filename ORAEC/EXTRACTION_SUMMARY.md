# ORAEC Coptic Etymologies - Extraction Summary

## Extraction Complete ✓

Successfully extracted and processed **2,177 etymological relationships** between Coptic, Egyptian, and Demotic words.

### Data Sources

1. **CSV File** from GitHub repository `oraec/coptic_etymologies`
   - Contains ID mappings between databases
   - 2,177 total entries

2. **HTML Table** from blog post (partial - sample only)
   - Contains word forms in Coptic, Egyptian, and Demotic scripts
   - 38 sample entries extracted

### Statistics

| Category | Count | Percentage |
|----------|-------|------------|
| **Total Entries** | 2,177 | 100.0% |
| With Egyptian ID | 1,695 | 77.9% |
| With Demotic ID | 1,827 | 83.9% |
| With Both IDs | 1,345 | 61.8% |
| Egyptian Only | 350 | 16.1% |
| Demotic Only | 482 | 22.1% |

### Files Created

1. **`coptic_etymologies_complete.json`**
   - Full dataset in JSON format
   - Pretty-printed with indentation
   - UTF-8 encoding for Coptic/Egyptian/Demotic scripts

2. **`coptic_etymologies_complete.jsonl`**
   - Same data in JSON Lines format
   - One entry per line
   - Easier for streaming/batch processing

3. **`statistics.json`**
   - Detailed statistics about the dataset

### Data Structure

Each entry contains:
```json
{
  "coptic_id": "C5",
  "egyptian_id": "854495",
  "demotic_id": null,
  "coptic_url": "https://coptic-dictionary.org/entry.cgi?tla=C5",
  "egyptian_url": "https://oraec.github.io/corpus/854495.html",
  "demotic_url": null,
  "coptic_word": "ⲁ-",
  "egyptian_word": "ꜥ.t",
  "demotic_word": null
}
```

### URL Mappings

All entries include direct URLs to:
- **Coptic Dictionary Online**: `https://coptic-dictionary.org/entry.cgi?tla={coptic_id}`
- **ORAEC Egyptian Corpus**: `https://oraec.github.io/corpus/{egyptian_id}.html`
- **TLA Demotic Database**: `https://aaew.bbaw.de/tla/servlet/GetWcnDetails?&wn={demotic_id}&db=1`

### Example Entries

1. **ⲁⲉⲓⲕ** (C24)
   - Egyptian: ꜥq.y (ID: 41430)
   - Demotic: ꜥyq (ID: 875)

2. **ⲁⲙⲓⲛ** (C89) "verily, indeed"
   - Egyptian: mn (ID: 69630)
   - Demotic: mn (ID: 2424)

3. **ⲁⲛⲟⲕ** (C135) "I" (1st person singular pronoun)
   - Egyptian: jnk (ID: 27940)
   - Demotic: jnky (ID: 590)

### Note on Word Forms

The current extraction includes ID mappings for all 2,177 entries, but word forms (actual Coptic/Egyptian/Demotic text) are only available for 38 sample entries from the blog post. 

To get complete word forms, one would need to:
1. Query the Coptic Dictionary Online API/website for each Coptic ID
2. Query ORAEC for Egyptian word forms
3. Query TLA for Demotic word forms

This could be automated but would require additional web scraping or API access.

### Research Value

This dataset enables:
- **Linguistic Research**: Trace word evolution across Egyptian language stages
- **Comparative Analysis**: Study phonological changes from Egyptian → Demotic → Coptic
- **Etymology Studies**: Understand semantic shifts across millennia
- **Digital Humanities**: Build etymological visualization tools
- **Language Learning**: Connect Coptic vocabulary to older Egyptian forms

### License

The data is licensed under **CC0 1.0 Universal** (Public Domain Dedication) by the ORAEC project.

### Citation

If using this data, cite:
- ORAEC Project: https://oraec.github.io/
- Blog Post: https://oraec.github.io/2024/08/17/digitization-of-coptic-etymologies.html
- GitHub Repository: https://github.com/oraec/coptic_etymologies

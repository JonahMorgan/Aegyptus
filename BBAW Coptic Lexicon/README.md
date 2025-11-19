# BBAW Coptic Lexicon parser

This script extracts lexicon entries from the TEI XML `BBAW_Lexicon_of_Coptic_Egyptian-v4-2020.xml` into JSON and JSONL.

Usage

1. Install dependencies (preferably in a virtualenv):

   pip install -r requirements.txt

2. Run the parser (defaults to the XML file in this folder):

   python parse_bbaw_lexicon.py

Optional: parse only first N entries for testing:

   python parse_bbaw_lexicon.py --limit 100

Output

- `bbaw_lexicon.jsonl` — newline-delimited JSON (one entry per line)
- `bbaw_lexicon.json` — array of entries

Fields

- `id` — TEI `xml:id` of the entry
- `type` — entry @type if present
- `forms` — list of forms with `id`, `type`, `orth`, `usg` (list), `gram` (pos/subc/note)
- `senses` — list of senses with `id`, `translations` (map lang->text), and `bibl` if present

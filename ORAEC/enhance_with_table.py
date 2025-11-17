"""
Enhance ORAEC etymology entries with full word forms from the blog table.

This script fetches the COMPLETE HTML/Markdown table from the ORAEC blog post
and merges all available Coptic/Egyptian/Demotic word forms into the existing
`coptic_etymologies_complete.json` dataset. It no longer relies on a partial,
hardcoded snippet and instead retrieves the full table dynamically, with a
local cache fallback.
"""

import json
import re
import sys
import html as htmlmod
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# Define paths
ORAEC_DIR = Path(r'c:\Users\user\Desktop\Aegyptus Transformer\Aegyptus Data\ORAEC')
INPUT_JSON = ORAEC_DIR / 'coptic_etymologies_complete.json'
OUTPUT_JSON = ORAEC_DIR / 'coptic_etymologies_enhanced.json'
OUTPUT_JSONL = ORAEC_DIR / 'coptic_etymologies_enhanced.jsonl'
BLOG_URL = 'https://oraec.github.io/2024/08/17/digitization-of-coptic-etymologies.html'
CACHE_TXT = ORAEC_DIR / 'blog_table_cache.txt'

def fetch_blog_content(url: str) -> str:
    """Fetch the blog page content. Returns text or raises an exception."""
    req = Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; ORAEC-Fetch/1.0)'
    })
    with urlopen(req, timeout=30) as resp:
        raw = resp.read()
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return raw.decode('utf-8', errors='replace')

def load_blog_table_text() -> str:
    """Load the blog table text: try online fetch; fallback to local cache.

    On success, also refresh the local cache file for reproducibility.
    """
    # 1) Try online fetch
    try:
        print(f"Fetching blog table from: {BLOG_URL}")
        html = fetch_blog_content(BLOG_URL)
        # Persist cache for offline use
        try:
            CACHE_TXT.write_text(html, encoding='utf-8')
            print(f"Cached fetched page → {CACHE_TXT}")
        except Exception as e:
            print(f"Warning: failed to write cache: {e}")
        return html
    except (URLError, HTTPError, TimeoutError) as e:
        print(f"Warning: online fetch failed: {e}")
    except Exception as e:
        print(f"Warning: unexpected fetch error: {e}")

    # 2) Fallback to cache if available
    if CACHE_TXT.exists():
        print(f"Loading blog table from cache: {CACHE_TXT}")
        return CACHE_TXT.read_text(encoding='utf-8', errors='replace')

    # 3) Nothing available
    raise RuntimeError(
        "Could not retrieve blog table content (network and cache unavailable)."
    )

def _clean_text(s: str) -> str:
    """Normalize whitespace and strip markdown artifacts."""
    if not s:
        return s
    # Normalize non-breaking spaces and multiple spaces
    s = s.replace('\u00A0', ' ').replace('&nbsp;', ' ')
    s = re.sub(r'\s+', ' ', s).strip()
    # Strip surrounding markdown asterisks or bullets
    s = s.strip('*').strip('•')
    return s

def parse_table_line(line: str):
    """Parse a single markdown-style table line into an entry dict.

    Expected normalized form (pipes optional at ends):
      COPTIC (ID:C123) | EGYPTIAN | DEMOTIC
    """
    if 'ID:' not in line or '|' not in line:
        return None

    # Remove leading/trailing pipes and extra spaces
    norm = line.strip()
    norm = re.sub(r'^\|\s*', '', norm)
    norm = re.sub(r'\s*\|\s*$', '', norm)
    parts = [
        _clean_text(p) for p in norm.split('|')
    ]
    if len(parts) < 1:
        return None

    # Extract Coptic word and ID from first column
    m = re.search(r'(.+?)\s*\(ID:([^)]+)\)', parts[0])
    if not m:
        return None
    coptic_word = _clean_text(m.group(1))
    coptic_id = _clean_text(m.group(2))

    # Egyptian and Demotic columns (may be missing)
    egyptian_word = _clean_text(parts[1]) if len(parts) > 1 and _clean_text(parts[1]) else None
    demotic_word = _clean_text(parts[2]) if len(parts) > 2 and _clean_text(parts[2]) else None

    return {
        'coptic_id': coptic_id,
        'coptic_word': coptic_word or None,
        'egyptian_word': egyptian_word,
        'demotic_word': demotic_word,
    }

def extract_entries_from_text(text: str):
    """Scan the fetched page text and extract all table lines into entries.

    This is robust to both HTML and markdown renditions because it operates on
    text lines containing pipes and the 'ID:' marker.
    """
    entries = []
    # Normalize line endings
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        # Heuristic: skip header/separator lines (e.g., '|' only)
        if line.count('|') < 2:
            continue
        if 'ID:' not in line:
            continue
        # Avoid false positives like table headers with empty columns
        candidate = parse_table_line(line)
        if candidate:
            entries.append(candidate)
    return entries

def _strip_tags(s: str) -> str:
    """Remove HTML tags and unescape entities."""
    if not s:
        return s
    # Remove tags
    s = re.sub(r'<[^>]+>', '', s)
    # Unescape entities
    s = htmlmod.unescape(s)
    return s

def extract_entries_from_html_table(html: str):
    """Parse <table> rows and cells to extract entries when content is HTML."""
    results = []
    # Find all table rows
    for row in re.findall(r'<tr[^>]*>(.*?)</tr>', html, flags=re.I | re.S):
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, flags=re.I | re.S)
        if not cells:
            continue
        cells_text = [_clean_text(_strip_tags(c)) for c in cells]
        if not cells_text or 'ID:' not in (cells_text[0] or ''):
            continue
        # Compose a pipe-separated pseudo-line and reuse the parser
        pseudo = ' | '.join(cells_text)
        entry = parse_table_line(pseudo)
        if entry:
            results.append(entry)
    return results

def main():
    print("Loading existing etymological data...")
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        existing_data = json.load(f)
    
    print(f"Loaded {len(existing_data)} existing entries")
    
    # Create lookup by Coptic ID
    data_by_id = {entry['coptic_id']: entry for entry in existing_data}
    
    # Fetch and parse table data
    print("\nFetching and parsing blog table data...")
    try:
        page_text = load_blog_table_text()
    except Exception as e:
        print(f"ERROR: {e}")
        print("Exiting without changes. Try running again with internet access, or place the blog HTML in 'blog_table_cache.txt'.")
        sys.exit(1)

    table_entries = extract_entries_from_text(page_text)
    # If none found via markdown-like scanning, try HTML table parsing
    if not table_entries:
        table_entries = extract_entries_from_html_table(page_text)
    print(f"Parsed {len(table_entries)} entries from blog table")
    
    # Update existing data with word forms
    updated_count = 0
    for table_entry in table_entries:
        coptic_id = table_entry['coptic_id']
        if coptic_id in data_by_id:
            # Update with word forms
            data_by_id[coptic_id]['coptic_word'] = table_entry['coptic_word']
            if table_entry['egyptian_word']:
                data_by_id[coptic_id]['egyptian_word'] = table_entry['egyptian_word']
            if table_entry['demotic_word']:
                data_by_id[coptic_id]['demotic_word'] = table_entry['demotic_word']
            updated_count += 1
    
    print(f"Updated {updated_count} entries with word forms")
    
    # Convert back to list
    enhanced_data = list(data_by_id.values())
    enhanced_data.sort(key=lambda x: int(x['coptic_id'][1:]) if x['coptic_id'][1:].isdigit() else 999999)
    
    # Save enhanced data
    print("\nSaving enhanced data...")
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(enhanced_data, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved: {OUTPUT_JSON}")
    
    with open(OUTPUT_JSONL, 'w', encoding='utf-8') as f:
        for entry in enhanced_data:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    print(f"✓ Saved: {OUTPUT_JSONL}")
    
    # Statistics
    stats = {
        'total': len(enhanced_data),
        'with_coptic_word': sum(1 for e in enhanced_data if e.get('coptic_word')),
        'with_egyptian_word': sum(1 for e in enhanced_data if e.get('egyptian_word')),
        'with_demotic_word': sum(1 for e in enhanced_data if e.get('demotic_word'))
    }
    
    print("\nStatistics:")
    print(f"  Total entries: {stats['total']}")
    print(f"  With Coptic word:   {stats['with_coptic_word']} ({stats['with_coptic_word']/stats['total']*100:.1f}%)")
    print(f"  With Egyptian word: {stats['with_egyptian_word']} ({stats['with_egyptian_word']/stats['total']*100:.1f}%)")
    print(f"  With Demotic word:  {stats['with_demotic_word']} ({stats['with_demotic_word']/stats['total']*100:.1f}%)")
    
    print("\n✓ Enhancement complete!")

if __name__ == '__main__':
    main()

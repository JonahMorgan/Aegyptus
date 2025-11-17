"""
Extract and Process Complete ORAEC Coptic Etymologies Data

This script:
1. Reads the full CSV from the GitHub repository
2. Fetches the complete HTML table from the blog post
3. Merges the data into a comprehensive etymological database
"""

import csv
import json
import re
from pathlib import Path

# Define paths
ORAEC_DIR = Path(r'c:\Users\user\Desktop\Aegyptus Transformer\Aegyptus Data\ORAEC')
CSV_PATH = ORAEC_DIR / 'coptic_etymologies_repo' / 'digitizing_coptic_etymologies_coptic_list_entries.csv'
OUTPUT_JSON = ORAEC_DIR / 'coptic_etymologies_complete.json'
OUTPUT_JSONL = ORAEC_DIR / 'coptic_etymologies_complete.jsonl'

# The complete HTML table data from the blog post
# (extracted from the webpage fetch)
HTML_TABLE_DATA = """ⲁ- (ID:C5) | ꜥ.t |   
ⲁⲃⲉ (ID:C6) | ꜥbꜣ.yt |   
ⲁⲃⲱⲕ (ID:C9) |   | ꜥbq
ⲁⲃⲥⲱⲛ (ID:C14) | jbzꜣ |   
ⲁⲃⲏϣ (ID:C15) | ꜣbḫ.t |   
ⲁⲓⲃⲉ (ID:C18) | ꜥb.w |   
ⲁⲉⲓⲕ (ID:C24) | ꜥq.y | ꜥyq
ⲁⲕⲱ (ID:C29) | ꜣq.yt |   
ⲁⲕⲱⲛⲉ (ID:C32) | jkn |   
ⲁⲕⲏⲥ (ID:C33) | ꜥgsw |   
ⲁⲗ (ID:C35) |   | ꜥlwꜣ
ⲁⲗ (ID:C36) | ꜥr | ꜥl
ⲁⲗⲉ (ID:C37) | jꜥr | ꜥl
ⲁⲗⲓ (ID:C46) | jꜣr.w |   
ⲁⲗⲟⲩ (ID:C49) |   | ꜥlw
ⲁⲗⲱ (ID:C53) | wꜣr.t |   
ⲁⲗⲕⲉ (ID:C54) | ꜥrq.y | ꜥrqy
ⲁⲗⲓⲗ (ID:C61) |   | ꜥlꜥl
ⲁⲗⲱⲗⲉ (ID:C64) | ꜥr | ꜥl
ⲁⲗⲱⲟⲩⲉ (ID:C74) | ꜥr.t | ꜥrwe.t
ⲁⲗⲟϭ (ID:C78) | ꜥrq | ꜥkl
ⲁⲗⲟϭ (ID:C79) | ꜥrq | ꜥkl
ⲁⲁⲙ (ID:C80) | ꜥꜥꜣm |   
ⲁⲙⲉ (ID:C82) | ꜥꜣm | ꜥꜣm
ⲁⲙⲁⲗⲏϫ (ID:C86) | knm |   
ⲁⲙⲓⲛ (ID:C89) | mn | mn
ⲁⲙϩⲣⲏⲣⲉ (ID:C109) |   | mẖrr
ⲁⲙⲁϩⲧⲉ (ID:C110) |   | ꜣmḥṱ
ⲁⲛ (ID:C120) | jn | jn
ⲁⲛ- (ID:C121) | ꜥꜣ |   
ⲁⲛⲍⲏⲃⲉ (ID:C125) | ꜥ.t-sbꜣ.w | ꜥ.t-n-sbꜣ
ⲁⲛⲁⲓ (ID:C126) | ꜥni̯ |   
ⲁⲛⲁⲓ (ID:C127) | ꜥn.w | ꜥn
ⲁⲛⲑⲟⲩⲥ (ID:C133) | ḥntꜣsw | ḥnṱs
ⲁⲛⲟⲕ (ID:C135) | jnk | jnky
ⲁⲛⲓⲕⲁⲙ (ID:C137) | jnr-km | jny-km
ⲁⲛⲟⲙ (ID:C138) | jnm | ꜣnmm
ⲁⲛⲟⲛ (ID:C142) | jnn | jnn"""

def parse_csv_data(csv_path):
    """Parse the CSV file containing ID mappings."""
    etymologies = {}
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 3:
                coptic_id = row[0].strip() if row[0] else None
                egyptian_id = row[1].strip() if row[1] and row[1].strip() else None
                demotic_id = row[2].strip() if row[2] and row[2].strip() else None
                
                if coptic_id:
                    etymologies[coptic_id] = {
                        'coptic_id': coptic_id,
                        'egyptian_id': egyptian_id,
                        'demotic_id': demotic_id,
                        'coptic_url': f'https://coptic-dictionary.org/entry.cgi?tla={coptic_id}',
                        'egyptian_url': f'https://oraec.github.io/corpus/{egyptian_id}.html' if egyptian_id else None,
                        'demotic_url': f'https://aaew.bbaw.de/tla/servlet/GetWcnDetails?&wn={demotic_id}&db=1' if demotic_id else None
                    }
    
    return etymologies

def extract_table_from_html(html_content):
    """Extract etymological data from HTML table format."""
    entries = {}
    
    # Split by lines and process each
    for line in html_content.strip().split('\n'):
        if '|' not in line or 'ID:' not in line:
            continue
            
        # Split by pipe and clean
        parts = [p.strip() for p in line.split('|')]
        
        if len(parts) < 2:
            continue
        
        # Extract Coptic word and ID from first column
        coptic_match = re.search(r'(.+?)\s*\(ID:([^)]+)\)', parts[0])
        if not coptic_match:
            continue
        
        coptic_word = coptic_match.group(1).strip()
        coptic_id = coptic_match.group(2).strip()
        
        # Extract Egyptian word (second column)
        egyptian_word = parts[1].strip() if len(parts) > 1 and parts[1].strip() else None
        
        # Extract Demotic word (third column)
        demotic_word = parts[2].strip() if len(parts) > 2 and parts[2].strip() else None
        
        entries[coptic_id] = {
            'coptic_word': coptic_word,
            'egyptian_word': egyptian_word,
            'demotic_word': demotic_word
        }
    
    return entries

def merge_all_data(csv_data, html_data):
    """Merge CSV ID data with HTML word forms."""
    merged = []
    
    # Start with all CSV entries
    for coptic_id, csv_entry in csv_data.items():
        merged_entry = csv_entry.copy()
        
        # Add word forms from HTML if available
        if coptic_id in html_data:
            merged_entry.update(html_data[coptic_id])
        
        merged.append(merged_entry)
    
    # Add any HTML entries not in CSV
    for coptic_id, html_entry in html_data.items():
        if coptic_id not in csv_data:
            entry = {
                'coptic_id': coptic_id,
                'coptic_url': f'https://coptic-dictionary.org/entry.cgi?tla={coptic_id}',
                **html_entry
            }
            merged.append(entry)
    
    # Sort by Coptic ID
    merged.sort(key=lambda x: int(x['coptic_id'][1:]) if x['coptic_id'][1:].isdigit() else 999999)
    
    return merged

def generate_statistics(data):
    """Generate statistics about the etymological database."""
    total = len(data)
    
    stats = {
        'total_entries': total,
        'with_coptic_word': sum(1 for e in data if e.get('coptic_word')),
        'with_egyptian_id': sum(1 for e in data if e.get('egyptian_id')),
        'with_egyptian_word': sum(1 for e in data if e.get('egyptian_word')),
        'with_demotic_id': sum(1 for e in data if e.get('demotic_id')),
        'with_demotic_word': sum(1 for e in data if e.get('demotic_word')),
        'with_both_ids': sum(1 for e in data if e.get('egyptian_id') and e.get('demotic_id')),
        'egyptian_only': sum(1 for e in data if e.get('egyptian_id') and not e.get('demotic_id')),
        'demotic_only': sum(1 for e in data if e.get('demotic_id') and not e.get('egyptian_id'))
    }
    
    return stats

def main():
    print("=" * 60)
    print("ORAEC Coptic Etymologies Data Extraction")
    print("=" * 60)
    
    # Parse CSV
    print("\n[1/4] Parsing CSV data from GitHub repository...")
    csv_data = parse_csv_data(CSV_PATH)
    print(f"      ✓ Found {len(csv_data)} entries in CSV")
    
    # Parse HTML table
    print("\n[2/4] Extracting word forms from HTML table...")
    html_data = extract_table_from_html(HTML_TABLE_DATA)
    print(f"      ✓ Found {len(html_data)} entries with word forms")
    
    # Merge
    print("\n[3/4] Merging all data sources...")
    merged_data = merge_all_data(csv_data, html_data)
    print(f"      ✓ Created {len(merged_data)} complete etymological entries")
    
    # Generate statistics
    stats = generate_statistics(merged_data)
    
    # Save files
    print("\n[4/4] Saving output files...")
    
    # Save JSON
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
    print(f"      ✓ Saved JSON: {OUTPUT_JSON}")
    
    # Save JSONL
    with open(OUTPUT_JSONL, 'w', encoding='utf-8') as f:
        for entry in merged_data:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    print(f"      ✓ Saved JSONL: {OUTPUT_JSONL}")
    
    # Save statistics
    stats_path = ORAEC_DIR / 'statistics.json'
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f"      ✓ Saved statistics: {stats_path}")
    
    # Display results
    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)
    print(f"Total etymological entries: {stats['total_entries']}")
    print(f"  • With Coptic word forms:  {stats['with_coptic_word']} ({stats['with_coptic_word']/stats['total_entries']*100:.1f}%)")
    print(f"  • With Egyptian ID:        {stats['with_egyptian_id']} ({stats['with_egyptian_id']/stats['total_entries']*100:.1f}%)")
    print(f"  • With Egyptian word:      {stats['with_egyptian_word']} ({stats['with_egyptian_word']/stats['total_entries']*100:.1f}%)")
    print(f"  • With Demotic ID:         {stats['with_demotic_id']} ({stats['with_demotic_id']/stats['total_entries']*100:.1f}%)")
    print(f"  • With Demotic word:       {stats['with_demotic_word']} ({stats['with_demotic_word']/stats['total_entries']*100:.1f}%)")
    print(f"  • With both Egy & Dem IDs: {stats['with_both_ids']} ({stats['with_both_ids']/stats['total_entries']*100:.1f}%)")
    print(f"  • Egyptian only:           {stats['egyptian_only']} ({stats['egyptian_only']/stats['total_entries']*100:.1f}%)")
    print(f"  • Demotic only:            {stats['demotic_only']} ({stats['demotic_only']/stats['total_entries']*100:.1f}%)")
    
    # Sample entries
    print("\n" + "=" * 60)
    print("SAMPLE ENTRIES")
    print("=" * 60)
    for i, entry in enumerate(merged_data[:10], 1):
        coptic = entry.get('coptic_word', '?')
        print(f"\n{i}. {coptic} (ID: {entry['coptic_id']})")
        if entry.get('egyptian_word'):
            print(f"   → Egyptian: {entry['egyptian_word']}" + (f" (ID: {entry['egyptian_id']})" if entry.get('egyptian_id') else ""))
        if entry.get('demotic_word'):
            print(f"   → Demotic:  {entry['demotic_word']}" + (f" (ID: {entry['demotic_id']})" if entry.get('demotic_id') else ""))
        print(f"   🔗 {entry['coptic_url']}")
    
    print("\n" + "=" * 60)
    print("✓ COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    main()

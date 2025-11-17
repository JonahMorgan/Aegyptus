"""
Parse ORAEC Coptic Etymologies Data

This script processes etymological data from:
1. The CSV file from the GitHub repository (ID mappings)
2. The HTML table from the blog post (word forms)

Output: Comprehensive JSON file with all etymological relationships
"""

import csv
import json
import re

def parse_csv_data(csv_path):
    """Parse the CSV file containing ID mappings."""
    etymologies = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 3:
                coptic_id = row[0].strip() if row[0] else None
                egyptian_id = row[1].strip() if row[1] else None
                demotic_id = row[2].strip() if row[2] else None
                
                entry = {
                    'coptic_id': coptic_id,
                    'egyptian_id': egyptian_id if egyptian_id else None,
                    'demotic_id': demotic_id if demotic_id else None,
                    'coptic_url': f'https://coptic-dictionary.org/entry.cgi?tla={coptic_id}' if coptic_id else None,
                    'egyptian_url': f'https://oraec.github.io/corpus/{egyptian_id}.html' if egyptian_id else None,
                    'demotic_url': f'https://aaew.bbaw.de/tla/servlet/GetWcnDetails?&wn={demotic_id}&db=1' if demotic_id else None
                }
                etymologies.append(entry)
    
    return etymologies

def parse_html_table_data():
    """Parse the HTML table data extracted from the blog post."""
    # This is the table data from the webpage
    table_data = """
ⲁ- (ID:C5) | ꜥ.t |  
ⲁⲃⲉ (ID:C6) | ꜥbꜣ.yt |  
ⲁⲃⲱⲕ (ID:C9) |  | ꜥbq
ⲁⲃⲥⲱⲛ (ID:C14) | jbzꜣ |  
ⲁⲃⲏϣ (ID:C15) | ꜣbḫ.t |  
ⲁⲓⲃⲉ (ID:C18) | ꜥb.w |  
ⲁⲉⲓⲕ (ID:C24) | ꜥq.y | ꜥyq
ⲁⲕⲱ (ID:C29) | ꜣq.yt |  
ⲁⲕⲱⲛⲉ (ID:C32) | jkn |  
ⲁⲕⲏⲥ (ID:C33) | ꜥgsw |  
ⲁⲗ (ID:C35) |  | ꜥlwꜣ
ⲁⲗ (ID:C36) | ꜥr | ꜥl
ⲁⲗⲉ (ID:C37) | jꜥr | ꜥl
ⲁⲗⲓ (ID:C46) | jꜣr.w |  
ⲁⲗⲟⲩ (ID:C49) |  | ꜥlw
ⲁⲗⲱ (ID:C53) | wꜣr.t |  
ⲁⲗⲕⲉ (ID:C54) | ꜥrq.y | ꜥrqy
ⲁⲗⲓⲗ (ID:C61) |  | ꜥlꜥl
ⲁⲗⲱⲗⲉ (ID:C64) | ꜥr | ꜥl
ⲁⲗⲱⲟⲩⲉ (ID:C74) | ꜥr.t | ꜥrwe.t
ⲁⲗⲟϭ (ID:C78) | ꜥrq | ꜥkl
ⲁⲗⲟϭ (ID:C79) | ꜥrq | ꜥkl
ⲁⲁⲙ (ID:C80) | ꜥꜥꜣm |  
ⲁⲙⲉ (ID:C82) | ꜥꜣm | ꜥꜣm
ⲁⲙⲁⲗⲏϫ (ID:C86) | knm |  
ⲁⲙⲓⲛ (ID:C89) | mn | mn
"""
    
    entries = []
    for line in table_data.strip().split('\n'):
        if '|' in line and 'ID:' in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3:
                # Extract Coptic word and ID
                coptic_match = re.search(r'(.*?)\s*\(ID:([^)]+)\)', parts[0])
                if coptic_match:
                    coptic_word = coptic_match.group(1).strip()
                    coptic_id = coptic_match.group(2).strip()
                    egyptian_word = parts[1].strip() if len(parts) > 1 and parts[1].strip() else None
                    demotic_word = parts[2].strip() if len(parts) > 2 and parts[2].strip() else None
                    
                    entries.append({
                        'coptic_id': coptic_id,
                        'coptic_word': coptic_word,
                        'egyptian_word': egyptian_word,
                        'demotic_word': demotic_word
                    })
    
    return entries

def merge_data(csv_entries, table_entries):
    """Merge CSV ID data with table word form data."""
    # Create a lookup dictionary from table entries
    table_lookup = {entry['coptic_id']: entry for entry in table_entries}
    
    merged = []
    for csv_entry in csv_entries:
        coptic_id = csv_entry['coptic_id']
        
        # Start with CSV data
        merged_entry = csv_entry.copy()
        
        # Add word forms from table if available
        if coptic_id in table_lookup:
            table_entry = table_lookup[coptic_id]
            merged_entry['coptic_word'] = table_entry.get('coptic_word')
            merged_entry['egyptian_word'] = table_entry.get('egyptian_word')
            merged_entry['demotic_word'] = table_entry.get('demotic_word')
        
        merged.append(merged_entry)
    
    return merged

def main():
    """Main processing function."""
    print("Parsing CSV data...")
    csv_path = r'c:\Users\user\Desktop\Aegyptus Transformer\Aegyptus Data\ORAEC\coptic_etymologies_repo\digitizing_coptic_etymologies_coptic_list_entries.csv'
    csv_entries = parse_csv_data(csv_path)
    print(f"Found {len(csv_entries)} entries in CSV")
    
    print("\nParsing HTML table data...")
    table_entries = parse_html_table_data()
    print(f"Found {len(table_entries)} entries from table")
    
    print("\nMerging data...")
    merged_data = merge_data(csv_entries, table_entries)
    
    # Save as JSON
    output_path = r'c:\Users\user\Desktop\Aegyptus Transformer\Aegyptus Data\ORAEC\coptic_etymologies_complete.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved {len(merged_data)} etymological entries to {output_path}")
    
    # Save as JSONL for easier processing
    jsonl_path = r'c:\Users\user\Desktop\Aegyptus Transformer\Aegyptus Data\ORAEC\coptic_etymologies_complete.jsonl'
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for entry in merged_data:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"Also saved as JSONL to {jsonl_path}")
    
    # Print some statistics
    print("\n=== Statistics ===")
    total = len(merged_data)
    with_egyptian = sum(1 for e in merged_data if e.get('egyptian_id'))
    with_demotic = sum(1 for e in merged_data if e.get('demotic_id'))
    with_both = sum(1 for e in merged_data if e.get('egyptian_id') and e.get('demotic_id'))
    with_word_forms = sum(1 for e in merged_data if e.get('coptic_word'))
    
    print(f"Total entries: {total}")
    print(f"With Egyptian etymology: {with_egyptian} ({with_egyptian/total*100:.1f}%)")
    print(f"With Demotic etymology: {with_demotic} ({with_demotic/total*100:.1f}%)")
    print(f"With both Egyptian and Demotic: {with_both} ({with_both/total*100:.1f}%)")
    print(f"With Coptic word forms: {with_word_forms} ({with_word_forms/total*100:.1f}%)")
    
    # Print first few examples
    print("\n=== Sample Entries ===")
    for i, entry in enumerate(merged_data[:5], 1):
        print(f"\n{i}. {entry.get('coptic_word', '?')} (ID: {entry['coptic_id']})")
        if entry.get('egyptian_word'):
            print(f"   Egyptian: {entry['egyptian_word']} (ID: {entry.get('egyptian_id', 'N/A')})")
        if entry.get('demotic_word'):
            print(f"   Demotic: {entry['demotic_word']} (ID: {entry.get('demotic_id', 'N/A')})")

if __name__ == '__main__':
    main()

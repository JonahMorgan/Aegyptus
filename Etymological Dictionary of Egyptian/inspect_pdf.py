"""
Diagnostic script to inspect the PDF structure and understand lemma formatting
"""

import fitz
import json

pdf_path = "Etymological-Dictionary-of-Egyptian.pdf"
doc = fitz.open(pdf_path)

# Let's inspect several pages to understand the structure
pages_to_check = [33, 34, 35, 36, 40]  # Check pages where lemma data starts (page 34 = index 33)

for page_num in pages_to_check:
    if page_num >= len(doc):
        continue
        
    print(f"\n{'='*70}")
    print(f"PAGE {page_num + 1}")
    print(f"{'='*70}")
    
    page = doc[page_num]
    text_dict = page.get_text("dict")
    
    # Look at more blocks to understand structure
    for i, block in enumerate(text_dict.get("blocks", [])[:15]):
        if block.get("type") == 0:  # Text block
            print(f"\n--- Block {i} ---")
            for j, line in enumerate(block.get("lines", [])[:5]):  # First 5 lines
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if text:
                        print(f"  [{j}] Text: '{text[:80]}'")
                        print(f"      Font: {span.get('font')}, Size: {span.get('size'):.1f}, Flags: {span.get('flags')}, Bold: {bool(span.get('flags', 0) & 16)}")

doc.close()
print("\n\nDone!")

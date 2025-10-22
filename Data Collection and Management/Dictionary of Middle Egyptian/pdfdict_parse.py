import pdfplumber
import re
import json
import logging
import os
import tempfile

# Set up logging
logging.basicConfig(
    filename="middle_egyptian_parse_errors.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def extract_column_text(page, verbose=False):
    """Extract text from both columns using crop."""
    page_height = page.height
    # Estimate column threshold based on word positions
    words = page.extract_words()
    if not words:
        print(f"Warning: No words extracted from page, using default threshold")
        return page.extract_text() or ""
    
    x_coords = [word['x0'] for word in words]
    column_threshold = sum(x_coords) / len(x_coords) if x_coords else page.width / 2
    
    left_crop = (0, 0, column_threshold, page_height)
    right_crop = (column_threshold, 0, page.width, page_height)
    
    left_text = page.crop(left_crop).extract_text() or ""
    right_text = page.crop(right_crop).extract_text() or ""
    
    combined_text = left_text + "\n" + right_text  # Combine with newline
    if verbose:
        print(f"Extracted column text (start): '{combined_text[:50]}...'")
    return combined_text

def parse_text(page_text, page_num, verbose=False):
    """Parse the accumulated page text and extract dictionary entries."""
    entries = []
    pos = 0
    last_pos = 0
    max_iterations = 1000  # Safeguard against infinite loop
    iteration = 0
    
    while len(entries) < 100 and pos < len(page_text) and iteration < max_iterations:
        # Look for potential entry start
        potential_match = re.search(r"\[[\w\s-]+\]", page_text[pos:])
        if not potential_match:
            if verbose and pos > last_pos:
                print(f"No potential entry found at pos {pos} on page {page_num}, text: '{page_text[pos:pos+50]}...'")
            pos += 10  # Aggressive advancement on failure
            iteration += 1
            continue
        
        start_pos = pos + potential_match.start()
        if verbose:
            print(f"Attempting match at pos {start_pos} on page {page_num}: '{page_text[start_pos:start_pos+50]}...'")
        
        # Match full entry with flexible definition
        match = re.search(r"\[(.*?)\]\s*((?:[^\[\]{}]+(?:\s+[^\[\]{}]+)*)?)\s*\{(.*?)\}", page_text[start_pos:], re.DOTALL)
        if not match:
            print(f"Unmatched entry on page {page_num} at pos {start_pos}: '{page_text[start_pos:start_pos+50]}...'")
            logging.info(f"Unmatched entry on page {page_num} at pos {start_pos}: '{page_text[start_pos:start_pos+50]}...'")
            pos = start_pos + 10  # Force advancement
            iteration += 1
            continue
        
        translit, definition, gardiner = match.groups()
        pos += match.start() + 1
        
        # Validate and clean
        translit = translit.strip()
        definition = re.sub(r"\s+", " ", definition.strip())  # Normalize spaces
        gardiner = gardiner.strip()
        
        if not translit or not gardiner:
            print(f"Skipped entry on page {page_num} at pos {pos} due to invalid translit '{translit}' or gardiner '{gardiner}': '{page_text[pos-20:pos+20]}'")
            logging.info(f"Skipped entry on page {page_num} at pos {pos} due to invalid translit '{translit}' or gardiner '{gardiner}': '{page_text[pos-20:pos+20]}'")
            pos += 1
            iteration += 1
            continue
        
        if re.search(r"[\[\]{}]", definition):
            print(f"Skipped entry on page {page_num} at pos {pos} due to invalid definition '{definition}': '{page_text[pos-20:pos+20]}'")
            logging.info(f"Skipped entry on page {page_num} at pos {pos} due to invalid definition '{definition}': '{page_text[pos-20:pos+20]}'")
            pos += 1
            iteration += 1
            continue
        
        entry = {
            "transliteration": translit,
            "definition": definition,
            "gardiner": gardiner,
            "page": page_num
        }
        print(f"Found entry on page {page_num} at pos {pos}: {entry}")
        logging.info(f"Parsed entry on page {page_num}: {entry}")
        entries.append(entry)
        pos += match.end()
        last_pos = pos
        iteration += 1
    
    if iteration >= max_iterations:
        print(f"Warning: Max iterations reached on page {page_num} at pos {pos}, possible infinite loop")
        logging.warning(f"Max iterations reached on page {page_num} at pos {pos}, possible infinite loop")
    
    return entries

def save_entries(entries, output_file):
    """Load existing entries, append new ones, and save to JSON file."""
    existing_entries = []
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_entries = json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: {output_file} is corrupted, starting fresh")
            logging.warning(f"{output_file} is corrupted, starting fresh")
    
    all_entries = existing_entries + entries
    print(f"Saving {len(all_entries)} total entries to {output_file}")
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".json") as temp_file:
            json.dump(all_entries, temp_file, ensure_ascii=False, indent=2)
        os.replace(temp_file.name, output_file)
        print(f"Successfully saved entries to {output_file}")
        logging.info(f"Saved {len(all_entries)} entries to {output_file}")
    except Exception as e:
        print(f"Error saving entries: {e}")
        logging.error(f"Error saving entries to {output_file}: {e}")
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)

def parse_pdf(pdf_path, verbose=False):
    """Parse the PDF page by page, accumulating text until a '}' is found."""
    output_file = "middle_egyptian_entries.json"
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"Processing {total_pages} pages starting from page 5...")
            logging.info(f"Starting PDF processing with {total_pages} pages")

            accumulated_text = ""
            current_page = 5
            while current_page <= total_pages:
                print(f"Extracting text from page {current_page}...")
                logging.info(f"Processing page {current_page}")
                
                # Extract text from both columns
                page = pdf.pages[current_page - 1]  # 0-based index
                page_text = extract_column_text(page, verbose)
                accumulated_text += page_text + " "
                accumulated_text = accumulated_text.strip().rstrip()  # Clean up whitespace
                
                # Debug: Print the last part of accumulated text
                if verbose:
                    print(f"Accumulated text: '{accumulated_text[-25] if accumulated_text else 'N/A'}'")
                
                # Check if the last character is '}'
                if accumulated_text.strip() and accumulated_text[-1] == '}':
                    print(f"Found end of accumulated text, parsing pages up to {current_page}...")
                    page_entries = parse_text(accumulated_text, current_page, verbose)
                    if page_entries:
                        save_entries(page_entries, output_file)
                    else:
                        print(f"No valid entries found for pages up to {current_page}")
                    accumulated_text = ""  # Reset for next block
                else:
                    print(f"No end of page {current_page} found, accumulating...")
                
                
                current_page += 1
            
            # Handle any remaining text
            if accumulated_text:
                print(f"Parsing remaining text from page {current_page - 1}...")
                page_entries = parse_text(accumulated_text, current_page - 1, verbose)
                if page_entries:
                    save_entries(page_entries, output_file)
                else:
                    print(f"No valid entries found in remaining text up to page {current_page - 1}")
            
            print(f"Completed parsing all pages")
            logging.info(f"Completed parsing")
            return page_entries if 'page_entries' in locals() else []
    except Exception as e:
        print(f"Error processing PDF on page {current_page}: {e}")
        print(f"Debug: text snippet = '{accumulated_text[:50]}...' if 'accumulated_text' in locals() else 'N/A'")
        logging.error(f"Error processing PDF on page {current_page}: {e}")
        return []

def main():
    pdf_path = "DictionaryOfMiddleEgyptian.pdf"
    
    print(f"Checking for PDF file at {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        logging.error(f"PDF file not found at {pdf_path}")
        return
    
    print("Starting Middle Egyptian dictionary entry parsing...")
    logging.info("Starting Middle Egyptian dictionary parsing...")
    
    entries = parse_pdf(pdf_path, verbose=True)
    if entries:
        print(f"Done! Entries saved incrementally to middle_egyptian_entries.json")
    else:
        print("Failed to parse entries. Check logs for details.")

if __name__ == "__main__":
    main()
<<<<<<< HEAD:Data Collection and Management/Wiktionary/wiktionary_get.py
import json
import re
from typing import Dict, List, Optional

<<<<<<<< HEAD:Data Collection and Management/Wiktionary/wiktionary_get.py
=======
# Data from en.wiktionary.org, licensed under CC BY-SA 3.0.
import requests
import time
import json
from urllib.parse import quote
import mwparserfromhell
import logging
import os
import tempfile

>>>>>>> 04f749911f50ff6cdbdb590300e5605260efd1c2:Data Collection and Management/Wiktionary/Egyptian/wiktionary_get.py
# Set up logging
def setup_logging(language):
    log_file = f"wiktionary_{language.lower()}_errors.log"
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    return log_file

# API base URL for en.wiktionary.org
API_BASE = "https://en.wiktionary.org/w/api.php"

# Headers to mimic a polite browser request
HEADERS = {
<<<<<<< HEAD:Data Collection and Management/Wiktionary/wiktionary_get.py
    "User-Agent": "EgyptianLemmasScraper/1.0 (email here)",  # Replace with your info!
=======
    "User-Agent": "EgyptianLemmasScraper/1.0 (user@email.com)",  # Replace with your info!
>>>>>>> 04f749911f50ff6cdbdb590300e5605260efd1c2:Data Collection and Management/Wiktionary/Egyptian/wiktionary_get.py
    "Accept": "application/json",
    "Referer": "https://en.wiktionary.org/wiki/Category:{}_lemmas"
}

def get_category_members(category, limit=500):
    """Fetch all pages in a category, paginated."""
    members = []
    cmcontinue = None
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmlimit": limit,
            "format": "json"
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        try:
            response = requests.get(API_BASE, params=params, headers=HEADERS, timeout=10)
            handle_response(response, "categorymembers")
            data = response.json()
            if "error" in data:
                logging.error(f"API Error in categorymembers: {data['error']}")
                raise ValueError(f"API Error: {data['error']}")
            members.extend([m['title'] for m in data["query"]["categorymembers"]])
            if "continue" not in data:
                break
            cmcontinue = data["continue"]["cmcontinue"]
            time.sleep(1)  # Rate limit
        except (requests.RequestException, ValueError) as e:
            logging.error(f"Error fetching category members: {e}")
            time.sleep(5)  # Wait longer before retrying
            continue
    return members

def handle_response(response, context=""):
    """Handle and log response errors."""
    if response.status_code >= 400:
        logging.error(f"{context} - Status {response.status_code}: {response.text[:1000]}")
        response.raise_for_status()

def get_page_wikitext(title, retries=3):
    """Fetch full wikitext for a page with retries."""
    params = {
        "action": "query",
        "titles": title,
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "formatversion": "2",
        "format": "json"
<<<<<<< HEAD:Data Collection and Management/Wiktionary/wiktionary_get.py
========
def parse_etymology_section(etymology_text: str, pos_level: int = 4) -> Dict:
    """
    Parse a single etymology section (including all its subsections).
    
    Args:
        etymology_text: The wikitext to parse
        pos_level: The heading level for POS sections (3 or 4 equals signs)
                  3 means === for POS (no etymology), 4 means ==== for POS (with etymology)
    """
    parsed = {
        'etymology_text': '',
        'definitions': [],
>>>>>>>> 04f749911f50ff6cdbdb590300e5605260efd1c2:Data Collection and Management/Wiktionary/Egyptian/wiktionary_parse.py
    }
    
    # Determine subsection level (one more = than POS level)
    subsection_level = pos_level + 1
    pos_marker = '=' * pos_level
    subsection_marker = '=' * subsection_level
    
    # Extract the etymology text itself (text before any POS sections)
    pos_pattern = rf'^(.*?)(?={pos_marker}(?:Noun|Verb|Adjective|Adverb|Particle|Proper noun|Preposition|Pronoun|Numeral){pos_marker})'
    etym_match = re.match(pos_pattern, etymology_text, re.DOTALL)
    if etym_match:
        parsed['etymology_text'] = etym_match.group(1).strip()
    else:
        # No POS sections found, might be just etymology text
        if not re.search(rf'{pos_marker}(?:Noun|Verb|Adjective|Adverb|Particle|Proper noun|Preposition|Pronoun|Numeral){pos_marker}', etymology_text):
            parsed['etymology_text'] = etymology_text.strip()
            return parsed
    
    # Extract definitions by part of speech
    # Split by POS headers to get each POS section
    pos_split_pattern = rf'({pos_marker}\s*(?:Noun|Verb|Adjective|Adverb|Particle|Proper noun|Preposition|Pronoun|Numeral)\s*{pos_marker})'
    pos_sections = re.split(pos_split_pattern, etymology_text, flags=re.IGNORECASE)
    
    # Process pairs of (header, content)
    for i in range(1, len(pos_sections), 2):
        if i + 1 >= len(pos_sections):
            break
            
        header = pos_sections[i]
        content = pos_sections[i + 1]
        
        # Extract POS name from header
        pos_match = re.search(rf'{pos_marker}\s*(Noun|Verb|Adjective|Adverb|Particle|Proper noun|Preposition|Pronoun|Numeral)\s*{pos_marker}', header, re.IGNORECASE)
        if not pos_match:
            continue
        pos = pos_match.group(1)
        
        # Extract template parameters
        template_match = re.search(r'^\s*\{\{egy-[^|]+\|([^}]*)\}\}', content, re.MULTILINE)
        params = template_match.group(1) if template_match else ''
        
        # Use the full content - the split already separated by POS sections correctly
        pos_content = content
        
        definition_entry = {
            'part_of_speech': pos.lower(),
            'parameters': params,
            'definitions': []
        }
        
        # Extract individual definitions (lines starting with # at beginning of line)
        definition_lines = re.findall(r'^#\s+(.+?)$', pos_content, re.MULTILINE)
        
        for defn in definition_lines:
            # Skip sub-definitions (those starting with another #)
            if defn.strip().startswith('#'):
                continue
            
            # Clean up wiki markup but preserve some structure
            clean_defn = re.sub(r'\{\{lb\|egy\|([^}]+)\}\}', r'[\1]', defn)  # Labels
            clean_defn = re.sub(r'\{\{defdate\|([^}]+)\}\}', r'(dated: \1)', clean_defn)
            clean_defn = re.sub(r'\{\{ng\|([^}]+)\}\}', r'\1', clean_defn)  # Non-gloss
            clean_defn = re.sub(r'\{\{def-uncertain\|[^}]+\}\}', '[uncertain]', clean_defn)
            clean_defn = re.sub(r'\{\{alt form\|egy\|([^}|]+)(?:\|([^}]+))?\}\}', r'Alternative form of \1', clean_defn)
            clean_defn = re.sub(r'\{\{alternative form of\|egy\|([^}|]+)(?:\|([^}]+))?\}\}', r'Alternative form of \1', clean_defn)
            clean_defn = re.sub(r'\{\{only used in\|egy\|([^}]+)\}\}', r'Only used in \1', clean_defn)
            clean_defn = re.sub(r'\{\{m\|egy\|([^}|]+)(?:\|[^}]*)?\}\}', r'\1', clean_defn)  # Mentions
            clean_defn = re.sub(r'\{\{[^}]+\}\}', '', clean_defn)  # Remove remaining templates
            clean_defn = re.sub(r'\[\[([^|\]]+)\|([^\]]+)\]\]', r'\2', clean_defn)  # Wiki links with text
            clean_defn = re.sub(r'\[\[([^\]]+)\]\]', r'\1', clean_defn)  # Simple wiki links
            clean_defn = re.sub(r"'''([^']+)'''", r'\1', clean_defn)  # Bold
            clean_defn = re.sub(r"''([^']+)''", r'\1', clean_defn)  # Italic
            clean_defn = re.sub(r'<sup>\?</sup>', '?', clean_defn)  # Superscript question marks
            clean_defn = re.sub(r'<[^>]+>', '', clean_defn)  # Remove HTML tags
            definition_entry['definitions'].append(clean_defn.strip())
        
        # Extract inflection for this POS (using subsection level)
        inflection_pattern = rf'{subsection_marker}Inflection{subsection_marker}\s*\n(\{{\{{[^}}]+\}}\}})'
        inflection_match = re.search(inflection_pattern, pos_content, re.DOTALL)
        if inflection_match:
            # Extract the template content - everything after "{{egy-" and before the closing "}}"
            template = inflection_match.group(1)
            # Extract parameters after the first |
            param_match = re.search(r'\{\{egy-[^|]+\|(.+)\}\}', template)
            if param_match:
                definition_entry['inflection'] = param_match.group(1)
        
        # Extract alternative forms for this POS
        alt_forms_pattern = rf'{subsection_marker}Alternative forms{subsection_marker}\s*\n(.*?)(?={subsection_marker}|\Z)'
        alt_forms_match = re.search(alt_forms_pattern, pos_content, re.DOTALL)
        if alt_forms_match:
            alt_forms_section = alt_forms_match.group(1)
            
            # Extract all {{egy-hieroforms}} templates
            hieroforms_templates = re.findall(r'\{\{egy-hieroforms(.*?)\}\}', alt_forms_section, re.DOTALL)
            
            if hieroforms_templates:
                all_alt_forms = []
                
                for template in hieroforms_templates:
                    # Extract the title if present
                    title_match = re.search(r'\|title=([^|\n]+)', template)
                    template_title = title_match.group(1).strip() if title_match else None
                    
                    # Split by lines and process each form
                    lines = template.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if not line or line.startswith('|title='):
                            continue
                        
                        # Parse the line - format is |hieroglyphs|read#=translit|date#=date|note#=note
                        if line.startswith('|'):
                            line = line[1:]  # Remove leading |
                        
                        # Split by | to get individual parameters
                        parts = line.split('|')
                        if not parts:
                            continue
                        
                        # First part is the hieroglyphs
                        hieroglyphs = parts[0].strip()
                        if not hieroglyphs:
                            continue
                        
                        # Parse other parameters
                        alt_form_entry = {
                            'hieroglyphs': hieroglyphs
                        }
                        
                        # Add template title if exists
                        if template_title:
                            alt_form_entry['title'] = template_title
                        
                        for part in parts[1:]:
                            if '=' in part:
                                key, value = part.split('=', 1)
                                key = key.strip()
                                value = value.strip()
                                
                                # Extract the number from read#, date#, note#
                                if key.startswith('read'):
                                    alt_form_entry['transliteration'] = value
                                elif key.startswith('date'):
                                    alt_form_entry['date'] = value
                                elif key.startswith('note'):
                                    alt_form_entry['note'] = value
                        
                        all_alt_forms.append(alt_form_entry)
                
                if all_alt_forms:
                    definition_entry['alternative_forms'] = all_alt_forms
        
        # Extract usage notes for this POS
        usage_pattern = rf'{subsection_marker}Usage notes{subsection_marker}\s*\n(.*?)(?={subsection_marker}|\Z)'
        usage_match = re.search(usage_pattern, pos_content, re.DOTALL)
        if usage_match:
            usage_text = usage_match.group(1).strip()
            # Clean up some markup
            usage_text = re.sub(r'\{\{m\|egy\|([^}|]+)(?:\|[^}]*)?\}\}', r'\1', usage_text)
            usage_text = re.sub(r'<div>(.*?)</div>', r'\1', usage_text, flags=re.DOTALL)
            usage_text = re.sub(r'\{\{w\|([^}|]+)(?:\|[^}]*)?\}\}', r'\1', usage_text)
            definition_entry['usage_notes'] = usage_text
        
        # Extract derived terms for this POS
        derived_pattern = rf'{subsection_marker}Derived terms{subsection_marker}\s*\n(.*?)(?={subsection_marker}|\Z)'
        derived_match = re.search(derived_pattern, pos_content, re.DOTALL)
        if derived_match:
            derived = re.findall(r'\{\{l\|egy\|([^}|]+)', derived_match.group(1))
            # Also extract from {{col|egy format
            col_terms = re.findall(r'^\|([^\n}]+)', derived_match.group(1), re.MULTILINE)
            derived.extend(col_terms)
            if derived:
                definition_entry['derived_terms'] = list(set([d.strip() for d in derived]))  # Remove duplicates
        
        # Extract descendants for this POS
        descendants_pattern = rf'{subsection_marker}Descendants{subsection_marker}\s*\n(.*?)(?={subsection_marker}|\Z)'
        descendants_match = re.search(descendants_pattern, pos_content, re.DOTALL)
        if descendants_match:
            descendants = re.findall(r'\{\{desc\|([^|]+)\|([^}|]+)', descendants_match.group(1))
            if descendants:
                definition_entry['descendants'] = [{'language': lang.strip(), 'word': word.strip()} for lang, word in descendants]
        
        parsed['definitions'].append(definition_entry)
    
    return parsed

def parse_wikitext_section(wikitext: str) -> Dict:
    """
    Parse a Wiktionary Egyptian section into structured data.
    Each etymology gets its own entry with associated definitions, forms, etc.
    """
    parsed = {
        'pronunciations': [],
        'etymologies': [],
        'related_terms': [],
        'see_also': [],
        'references': []
    }
    
    # Extract global pronunciation (before any etymology sections)
    pronunciation_section = re.search(r'===Pronunciation===\s*\n(.*?)(?====|$)', wikitext, re.DOTALL)
    if pronunciation_section:
        # Extract IPA transcriptions
        ipa_matches = re.findall(r'\{\{egy-IPA(?:-[ER])?\|?([^}]*)\}\}', pronunciation_section.group(1))
        parsed['pronunciations'] = ipa_matches
    
    # Split by etymology sections
    etymology_pattern = r'===Etymology\s*(\d+)?===\s*\n(.*?)(?====Etymology|\Z)'
    etymology_matches = re.findall(etymology_pattern, wikitext, re.DOTALL)
    
    if etymology_matches:
        # Multiple or numbered etymologies - POS sections use ====
        for etym_num, etym_content in etymology_matches:
            etym_entry = parse_etymology_section(etym_content, pos_level=4)
            etym_entry['etymology_number'] = int(etym_num) if etym_num else len(parsed['etymologies']) + 1
            parsed['etymologies'].append(etym_entry)
    else:
        # No explicit etymology sections - POS sections use ===
        # Look for POS sections at === level
        pos_sections = re.search(r'(===(?:Noun|Verb|Adjective|Adverb|Particle|Proper noun|Preposition)===.*)', wikitext, re.DOTALL)
        if pos_sections:
            etym_entry = parse_etymology_section(pos_sections.group(1), pos_level=3)
            etym_entry['etymology_number'] = None  # No explicit number
            parsed['etymologies'].append(etym_entry)
    
    # Extract global related terms (outside etymology sections)
    related_match = re.search(r'===Related terms===\s*\n(.*?)(?====|$)', wikitext, re.DOTALL)
    if related_match:
        related = re.findall(r'\{\{l\|egy\|([^}|]+)', related_match.group(1))
        parsed['related_terms'] = related
    
    # Extract see also
    see_also_match = re.search(r'===See also===\s*\n(.*?)(?====|$)', wikitext, re.DOTALL)
    if see_also_match:
        see_also = re.findall(r'\{\{l\|egy\|([^}|]+)', see_also_match.group(1))
        parsed['see_also'] = see_also
    
    # Extract references
    references_match = re.search(r'===References===\s*\n(.*?)(?====|$)', wikitext, re.DOTALL)
    if references_match:
        parsed['references'] = references_match.group(1).strip()
    
    return parsed

def parse_egyptian_lemmas(input_file: str, output_file: str):
    """
    Parse egyptian_lemmas.json and create a structured JSON output.
    """
    print(f"Loading data from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Found {len(data)} lemmas to parse...")
    
    parsed_data = {}
    
    for idx, (lemma, content) in enumerate(data.items()):
        if (idx + 1) % 100 == 0:
            # Avoid unicode errors in console output
            try:
                print(f"Processing lemma {idx + 1}/{len(data)}: {lemma}")
            except:
                print(f"Processing lemma {idx + 1}/{len(data)}")
        
        egyptian_section = content.get('egyptian_section', '')
        full_wikitext = content.get('full_wikitext', '')
        
        parsed_entry = parse_wikitext_section(egyptian_section)
        
        # Add original data
        parsed_entry['lemma'] = lemma
        parsed_entry['full_wikitext'] = full_wikitext
        parsed_entry['egyptian_section'] = egyptian_section
        
        parsed_data[lemma] = parsed_entry
    
    print(f"\nSaving parsed data to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(parsed_data, f, ensure_ascii=False, indent=2)
    
    print(f"Done! Parsed {len(parsed_data)} lemmas.")
    
    # Print sample entry
    if parsed_data:
        sample_lemma = list(parsed_data.keys())[0]
        print(f"\nSample parsed entry for '{sample_lemma}':")
        print(json.dumps(parsed_data[sample_lemma], ensure_ascii=False, indent=2)[:500] + "...")

def main():
    """
    Main function to parse egyptian_lemmas.json
    """
    import os
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, 'egyptian_lemmas.json')
    output_file = os.path.join(script_dir, 'egyptian_lemmas_parsed.json')
    
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        return
    
    parse_egyptian_lemmas(input_file, output_file)

if __name__ == "__main__":
    main()
=======
    }
    for attempt in range(retries):
        try:
            response = requests.get(API_BASE, params=params, headers=HEADERS, timeout=10)
            handle_response(response, f"Page fetch for {title}")
            data = response.json()
            if "error" in data:
                logging.error(f"API Error for {title}: {data['error']}")
                return None
            pages = data["query"]["pages"]
            if not pages:
                logging.warning(f"No pages returned for {title}")
                return None
            page = pages[0]
            if page.get("missing"):
                logging.warning(f"Page missing: {title}")
                return None
            if "revisions" not in page or not page["revisions"]:
                logging.warning(f"No revisions for {title}")
                return None
            rev = page["revisions"][0]
            if "slots" not in rev or "main" not in rev["slots"]:
                logging.error(f"No main slot for {title}: {json.dumps(page, ensure_ascii=False)}")
                return None
            slot = rev["slots"]["main"]
            if "content" not in slot:
                logging.error(f"No content for {title}: {json.dumps(page, ensure_ascii=False)}")
                return None
            return slot["content"]
        except (requests.RequestException, ValueError) as e:
            logging.error(f"Attempt {attempt + 1} failed for {title}: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logging.error(f"Failed to fetch {title} after {retries} attempts")
                return None
    return None

def extract_language_section(wikitext, title, language):
    """Parse wikitext and extract the language-specific section."""
    if not wikitext:
        return ""
    try:
        parsed = mwparserfromhell.parse(wikitext)
        for section in parsed.get_sections([language]):
            return str(section)
        logging.warning(f"No '{language}' section found for {title}")
        return wikitext
    except Exception as e:
        logging.error(f"Error parsing wikitext for {title}: {e}")
        return wikitext

def save_lemma(data, output_file, title):
    """Save a single lemma to the JSON file."""
    existing_data = {}
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception as e:
            logging.error(f"Error reading {output_file}: {e}")
    
    existing_data[title] = data
    
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".json") as temp_file:
        json.dump(existing_data, temp_file, ensure_ascii=False, indent=2)
    
    try:
        os.replace(temp_file.name, output_file)
        logging.info(f"Saved lemma {title} to {output_file}")
    except Exception as e:
        logging.error(f"Error replacing {output_file}: {e}")
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)

def load_lemmas_list(lemma_file):
    """Load lemma list from file if it exists."""
    if os.path.exists(lemma_file):
        with open(lemma_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_lemmas_list(lemmas, lemma_file):
    """Save lemma list to file."""
    with open(lemma_file, "w", encoding="utf-8") as f:
        json.dump(lemmas, f, ensure_ascii=False, indent=2)
    logging.info(f"Saved lemma list to {lemma_file}")

def main():
    # Prompt for language selection
    valid_languages = ["Coptic", "Egyptian", "Demotic"]
    print("Available languages: Coptic, Egyptian, Demotic")
    language = input("Enter language to scrape: ").strip().capitalize()
    if language not in valid_languages:
        print(f"Invalid language. Choose from: {', '.join(valid_languages)}")
        logging.error(f"Invalid language selected: {language}")
        return
    
    # Set up language-specific variables
    category = f"{language} lemmas"
    output_file = f"{language.lower()}_lemmas.json"
    lemma_file = f"{language.lower()}_lemmas_list.json"
    log_file = setup_logging(language)
    HEADERS["Referer"] = HEADERS["Referer"].format(language)  # Update Referer for language
    
    logging.info(f"Starting {language} lemma collection...")
    print(f"Checking for existing {language} lemma list...")
    lemmas = load_lemmas_list(lemma_file)
    
    if lemmas is None:
        print(f"Fetching list of {language} lemmas...")
        logging.info(f"Fetching list of {language} lemmas...")
        lemmas = get_category_members(category)
        save_lemmas_list(lemmas, lemma_file)
    else:
        print(f"Loaded {len(lemmas)} lemmas from {lemma_file}")
        logging.info(f"Loaded {len(lemmas)} lemmas from {lemma_file}")
    
    print(f"Found {len(lemmas)} lemmas.")
    logging.info(f"Found {len(lemmas)} lemmas.")
    
    # Load existing lemmas to skip processed ones
    processed_titles = set()
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                processed_titles = set(json.load(f).keys())
            print(f"Skipping {len(processed_titles)} already processed {language} lemmas.")
            logging.info(f"Skipping {len(processed_titles)} already processed {language} lemmas.")
        except Exception as e:
            logging.error(f"Error reading {output_file} for processed titles: {e}")
    
    total_processed = 0
    for i, title in enumerate(lemmas, 1):
        if title in processed_titles:
            print(f"Skipping {i}/{len(lemmas)}: {title} (already processed)")
            logging.info(f"Skipping {i}/{len(lemmas)}: {title} (already processed)")
            continue
        
        print(f"Processing {i}/{len(lemmas)}: {title}")
        logging.info(f"Processing {i}/{len(lemmas)}: {title}")
        wikitext = get_page_wikitext(title)
        if wikitext:
            language_section = extract_language_section(wikitext, title, language)
            lemma_data = {
                "full_wikitext": wikitext,
                f"{language.lower()}_section": language_section
            }
            save_lemma(lemma_data, output_file, title)
            total_processed += 1
        else:
            logging.warning(f"Skipped {title} due to fetch failure")
        time.sleep(1.5)  # Rate limit delay
    
    print(f"Done! Processed {total_processed} new {language} lemmas. Data saved to {output_file}")
    logging.info(f"Done! Processed {total_processed} new {language} lemmas. Data saved to {output_file}")

if __name__ == "__main__":
    main()
>>>>>>> 04f749911f50ff6cdbdb590300e5605260efd1c2:Data Collection and Management/Wiktionary/Egyptian/wiktionary_get.py

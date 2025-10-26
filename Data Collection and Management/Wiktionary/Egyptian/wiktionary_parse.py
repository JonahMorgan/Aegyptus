import json
import re
from typing import Dict, List, Optional

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

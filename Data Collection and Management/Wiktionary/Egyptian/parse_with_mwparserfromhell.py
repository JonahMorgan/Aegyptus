"""
Parser for Egyptian, Demotic, and Coptic Wiktionary lemmas using mwparserfromhell.
This is a cleaner, more robust implementation than regex-based parsing.
"""

import json
import mwparserfromhell
from typing import Dict, List, Optional
import sys
from pathlib import Path

def parse_template_params(template) -> Dict[str, str]:
    """Extract all parameters from a template as a dictionary."""
    params = {}
    for param in template.params:
        key = str(param.name).strip()
        value = str(param.value).strip()
        params[key] = value
    return params

def parse_egy_hieroforms(template) -> List[Dict[str, str]]:
    """Parse {{egy-hieroforms}} template into structured alternative forms."""
    params = parse_template_params(template)
    alt_forms = []
    
    # Extract title if present
    title = params.get('title')
    
    # Group parameters by number (read1, date1, note1, etc.)
    form_groups = {}
    hieroglyphs_by_index = {}
    
    # First, collect all numbered forms
    for i in range(1, 100):  # Reasonable upper limit
        read_key = f'read{i}'
        if read_key in params:
            form_groups[i] = {
                'transliteration': params[read_key]
            }
            if f'date{i}' in params:
                form_groups[i]['date'] = params[f'date{i}']
            if f'note{i}' in params:
                form_groups[i]['note'] = params[f'note{i}']
    
    # Find hieroglyphs - they're positional parameters (no name, just value)
    # They come before their corresponding read# parameter
    positional_params = []
    for param in template.params:
        if not str(param.name).strip() or str(param.name).strip().isdigit():
            hieroglyphs = str(param.value).strip()
            if hieroglyphs and hieroglyphs not in ['title']:
                positional_params.append(hieroglyphs)
    
    # Match hieroglyphs to forms (they should be in order)
    for i, (form_num, form_data) in enumerate(sorted(form_groups.items())):
        if i < len(positional_params):
            form_entry = {
                'hieroglyphs': positional_params[i]
            }
            form_entry.update(form_data)
            if title:
                form_entry['title'] = title
            alt_forms.append(form_entry)
    
    return alt_forms

def extract_definitions(wikicode, level: int = 1) -> List[str]:
    """Extract definition lines (starting with #) at a specific nesting level."""
    definitions = []
    text = str(wikicode)
    
    for line in text.split('\n'):
        # Count leading # characters
        stripped = line.lstrip()
        if not stripped.startswith('#'):
            continue
        
        hash_count = len(line) - len(line.lstrip('#'))
        if hash_count == level:
            # Remove the # and clean up
            defn = stripped[1:].strip()
            
            # Parse the definition to clean up templates
            defn_code = mwparserfromhell.parse(defn)
            
            # Clean up common templates - iterate over a list copy to avoid modification issues
            templates = list(defn_code.filter_templates())
            for template in templates:
                try:
                    name = str(template.name).strip()
                    if name == 'lb':
                        # Labels like {{lb|egy|intransitive}}
                        labels = [str(p.value).strip() for p in template.params[1:]]
                        defn_code.replace(template, f"[{', '.join(labels)}]")
                    elif name == 'defdate':
                        params = parse_template_params(template)
                        date_str = list(params.values())[0] if params else ''
                        defn_code.replace(template, f"(dated: {date_str})")
                    elif name == 'ng':
                        # Non-gloss definition
                        params = parse_template_params(template)
                        defn_code.replace(template, list(params.values())[0] if params else '')
                    elif name == 'def-uncertain':
                        defn_code.replace(template, '[uncertain]')
                    elif name in ['alt form', 'alternative form of', 'altform']:
                        # Alternative form templates - preserve the information
                        params = parse_template_params(template)
                        values = list(params.values())
                        term = values[1] if len(values) > 1 else values[0] if values else ''
                        defn_code.replace(template, f"Alternative form of {term}")
                    elif name in ['m', 'l', 'w', 'taxfmt', 'cog', 'inh']:
                        # Link templates - just extract the linked term
                        params = parse_template_params(template)
                        values = list(params.values())
                        defn_code.replace(template, values[1] if len(values) > 1 else values[0] if values else '')
                    elif name == 'q':
                        # Qualifier
                        params = parse_template_params(template)
                        defn_code.replace(template, ' '.join(params.values()))
                    elif name == 'sup':
                        defn_code.replace(template, '')
                except (ValueError, AttributeError):
                    # Template already replaced or other issue, skip
                    pass
            
            # Remove any remaining HTML tags
            clean_text = str(defn_code).strip()
            clean_text = mwparserfromhell.parse(clean_text).strip_code()
            
            if clean_text:
                definitions.append(clean_text)
    
    return definitions

def parse_pos_section(section_code, pos_name: str, subsection_level: int) -> Dict:
    """Parse a single part-of-speech section."""
    result = {
        'part_of_speech': pos_name.lower(),
        'parameters': '',
        'definitions': []
    }
    
    # Find the POS template (e.g., {{egy-verb|...}}, {{egy-noun|...}})
    for template in section_code.filter_templates():
        name = str(template.name).strip()
        if name.startswith('egy-') or name.startswith('cop-') or name.startswith('dem-'):
            if any(pos.lower() in name.lower() for pos in ['noun', 'verb', 'adj', 'adv', 'part', 'prep', 'pron', 'num', 'proper']):
                params = parse_template_params(template)
                # Join all parameters into a string
                result['parameters'] = '|'.join(f"{k}={v}" if k else v for k, v in params.items())
                break
    
    # Extract definitions
    result['definitions'] = extract_definitions(section_code, level=1)
    
    # Look for subsections
    sections = section_code.get_sections(levels=[subsection_level])
    
    for subsection in sections:
        heading = subsection.filter_headings()
        if not heading:
            continue
        
        heading_text = str(heading[0].title).strip()
        
        # Inflection
        if heading_text == 'Inflection':
            for template in subsection.filter_templates():
                name = str(template.name).strip()
                if 'decl' in name or 'conj' in name:
                    params = parse_template_params(template)
                    # Extract just the parameters (skip the template name)
                    param_list = []
                    for k, v in params.items():
                        if k:  # Named parameter
                            param_list.append(f"{k}={v}" if k else v)
                        else:  # Positional parameter
                            param_list.append(v)
                    result['inflection'] = '|'.join(param_list)
                    break
        
        # Alternative forms
        elif heading_text == 'Alternative forms':
            alt_forms = []
            for template in subsection.filter_templates():
                name = str(template.name).strip()
                if 'hieroforms' in name:
                    # Egyptian hieroglyphic forms
                    forms = parse_egy_hieroforms(template)
                    alt_forms.extend(forms)
                elif name in ['alter', 'alt']:
                    # Simple alternative forms (used in Coptic/Demotic)
                    # Format: {{alter|lang|form1|form2|...|dialect}}
                    params = [str(p.value).strip() for p in template.params]
                    if len(params) < 2:
                        continue
                    
                    # Skip language code (first param)
                    forms_and_dialect = params[1:]
                    
                    # Last non-empty param might be a dialect
                    dialect = None
                    dialect_names = ['Akhmimic', 'Bohairic', 'Sahidic', 'Fayyumic', 'Lycopolitan']
                    
                    # Find forms and potential dialect
                    forms_in_template = []
                    for val in forms_and_dialect:
                        if val:  # Non-empty
                            if val in dialect_names:
                                dialect = val
                            else:
                                forms_in_template.append(val)
                    
                    # Add each form
                    for form in forms_in_template:
                        form_entry = {'form': form}
                        if dialect:
                            form_entry['dialect'] = dialect
                        alt_forms.append(form_entry)
            
            if alt_forms:
                result['alternative_forms'] = alt_forms
        
        # Usage notes
        elif heading_text == 'Usage notes':
            text = str(subsection).split('\n', 1)[1] if '\n' in str(subsection) else ''
            # Clean up templates
            cleaned = mwparserfromhell.parse(text)
            templates = list(cleaned.filter_templates())
            for template in templates:
                try:
                    name = str(template.name).strip()
                    if name in ['m', 'l', 'w']:
                        params = parse_template_params(template)
                        values = list(params.values())
                        cleaned.replace(template, values[1] if len(values) > 1 else values[0] if values else '')
                except (ValueError, AttributeError):
                    pass
            result['usage_notes'] = cleaned.strip_code().strip()
        
        # Derived terms
        elif heading_text == 'Derived terms':
            derived = []
            for template in subsection.filter_templates():
                name = str(template.name).strip()
                if name == 'l':
                    params = parse_template_params(template)
                    values = list(params.values())
                    if len(values) > 1:
                        derived.append(values[1])
                elif name == 'col':
                    # Column layout with terms
                    params = parse_template_params(template)
                    for v in list(params.values())[1:]:  # Skip language code
                        if v and not v.startswith('col'):
                            derived.append(v)
            if derived:
                result['derived_terms'] = list(set(derived))
        
        # Descendants
        elif heading_text == 'Descendants':
            descendants = []
            for template in subsection.filter_templates():
                name = str(template.name).strip()
                if name == 'desc':
                    params = parse_template_params(template)
                    values = list(params.values())
                    if len(values) >= 2:
                        descendants.append({
                            'language': values[0],
                            'word': values[1]
                        })
            if descendants:
                result['descendants'] = descendants
    
    return result

def parse_etymology_section(wikicode, etym_num: Optional[int] = None, pos_level: int = 4) -> Dict:
    """Parse a single etymology section."""
    result = {
        'etymology_text': '',
        'definitions': [],
        'etymology_number': etym_num
    }
    
    # Extract etymology text (before any POS sections)
    text_before_pos = []
    for node in wikicode.nodes:
        if hasattr(node, 'title') and str(node.title).strip() in [
            'Noun', 'Verb', 'Adjective', 'Adverb', 'Particle', 'Proper noun', 
            'Preposition', 'Pronoun', 'Numeral', 'Letter'
        ]:
            break
        text_before_pos.append(str(node))
    
    if text_before_pos:
        etym_text = ''.join(text_before_pos).strip()
        result['etymology_text'] = etym_text
    
    # Get POS sections
    pos_sections = wikicode.get_sections(levels=[pos_level])
    
    for section in pos_sections:
        headings = section.filter_headings()
        if not headings:
            continue
        
        pos_name = str(headings[0].title).strip()
        if pos_name in ['Noun', 'Verb', 'Adjective', 'Adverb', 'Particle', 'Proper noun', 
                        'Preposition', 'Pronoun', 'Numeral', 'Letter']:
            pos_data = parse_pos_section(section, pos_name, pos_level + 1)
            result['definitions'].append(pos_data)
    
    return result

def parse_wikitext(wikitext: str, language: str = 'Egyptian') -> Dict:
    """Parse complete wikitext for a lemma entry."""
    wikicode = mwparserfromhell.parse(wikitext)
    
    result = {
        'pronunciations': [],
        'etymologies': [],
        'related_terms': [],
        'see_also': [],
        'references': ''
    }
    
    # Find the language section
    sections = wikicode.get_sections(levels=[2])
    lang_section = None
    
    for section in sections:
        headings = section.filter_headings()
        if headings and str(headings[0].title).strip() == language:
            lang_section = section
            break
    
    if not lang_section:
        return result
    
    # Extract pronunciation
    pronunciation_sections = lang_section.get_sections(matches='Pronunciation')
    for pron_section in pronunciation_sections:
        for template in pron_section.filter_templates():
            name = str(template.name).strip()
            if 'IPA' in name or 'pron' in name.lower():
                params = parse_template_params(template)
                result['pronunciations'].append('|'.join(f"{k}={v}" for k, v in params.items()))
    
    # Check if there are etymology sections
    etym_sections = lang_section.get_sections(matches=lambda x: 'Etymology' in str(x))
    
    if etym_sections and any('Etymology 1' in str(s) or 'Etymology 2' in str(s) for s in etym_sections):
        # Multiple etymologies - use level 4 (====) for POS
        for i in range(1, 20):  # Reasonable limit
            etym_title = f'Etymology {i}'
            etym_section = lang_section.get_sections(matches=etym_title)
            if etym_section:
                parsed = parse_etymology_section(etym_section[0], etym_num=i, pos_level=4)
                result['etymologies'].append(parsed)
            else:
                break
    else:
        # Single etymology or no explicit etymology section - use level 3 (===) for POS
        parsed = parse_etymology_section(lang_section, pos_level=3)
        result['etymologies'].append(parsed)
    
    # Extract references
    ref_sections = lang_section.get_sections(matches='References')
    if ref_sections:
        result['references'] = str(ref_sections[0]).split('\n', 1)[1].strip() if '\n' in str(ref_sections[0]) else ''
    
    return result

def main():
    """Parse all Egyptian, Demotic, and Coptic lemma files."""
    
    base_dir = Path(__file__).parent
    
    # Define files to process
    files_to_process = [
        ('egyptian_lemmas.json', 'egyptian_lemmas_parsed_mwp.json', 'Egyptian'),
        ('demotic_lemmas.json', 'demotic_lemmas_parsed_mwp.json', 'Demotic'),
        ('coptic_lemmas.json', 'coptic_lemmas_parsed_mwp.json', 'Coptic')
    ]
    
    for input_file, output_file, language in files_to_process:
        input_path = base_dir / input_file
        output_path = base_dir / output_file
        
        if not input_path.exists():
            print(f"Skipping {input_file} - file not found")
            continue
        
        print(f"\nProcessing {input_file}...")
        print(f"Loading data...")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Found {len(data)} lemmas to parse...")
        
        parsed_data = {}
        
        for idx, (lemma, content) in enumerate(data.items()):
            if (idx + 1) % 100 == 0:
                try:
                    print(f"Processing lemma {idx + 1}/{len(data)}: {lemma}")
                except:
                    print(f"Processing lemma {idx + 1}/{len(data)}")
            
            # Get the appropriate section
            section_key = f'{language.lower()}_section'
            wikitext = content.get(section_key, content.get('full_wikitext', ''))
            
            # Parse the wikitext
            parsed = parse_wikitext(wikitext, language)
            
            # Add metadata
            parsed['lemma'] = lemma
            parsed['full_wikitext'] = content.get('full_wikitext', '')
            parsed[section_key] = wikitext
            
            parsed_data[lemma] = parsed
        
        # Save parsed data
        print(f"Saving parsed data to {output_file}...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=2)
        
        print(f"Done! Parsed {len(parsed_data)} lemmas.")
        
        # Show sample
        if parsed_data:
            first_lemma = next(iter(parsed_data.keys()))
            print(f"\nSample parsed entry for '{first_lemma}':")
            print(json.dumps(parsed_data[first_lemma], indent=2, ensure_ascii=False)[:500])
            print("...\n")

if __name__ == '__main__':
    main()

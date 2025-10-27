import json
import re
import os
import tempfile
import logging

# Set up logging
logging.basicConfig(
    filename="test_parse_egyptian_lemma_errors.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def clean_text(text):
    """Clean text by removing extra newlines and leading/trailing whitespace."""
    return re.sub(r'\n+', ' ', text.strip()).strip()

def extract_definitions(section_text):
    """Extract definitions from lines starting with '#' or within <li> tags."""
    definitions = []
    lines = section_text.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('#'):
            cleaned = re.sub(r'{{[^}]+}}', '', line).lstrip('# ').strip()
            if cleaned:
                definitions.append(cleaned)
        elif line.startswith('<li>'):
            cleaned = re.sub(r'{{[^}]+}}', '', line).lstrip('<li>').rstrip('</li>').strip()
            if cleaned:
                definitions.append(cleaned)
    return definitions

def extract_hieroglyphs(section_text):
    """Extract hieroglyph codes from egy-h and egy-hieroforms templates."""
    hieroglyphs = []
    # Match egy-h templates
    egy_h_matches = re.findall(r'{{egy-h\|([^}]+)}}', section_text)
    for match in egy_h_matches:
        hiero = match.strip()
        if hiero and hiero not in hieroglyphs:
            hieroglyphs.append(hiero)
    
    # Match egy-hieroforms templates
    hieroforms_matches = re.findall(r'{{egy-hieroforms\|([^}]+)}}', section_text)
    for match in hieroforms_matches:
        params = match.split('|')
        for param in params:
            if not param.strip().startswith('read') and not param.strip().startswith('date') and not param.strip().startswith('note'):
                hiero = param.strip()
                if hiero and hiero not in hieroglyphs:
                    hieroglyphs.append(hiero)
    
    return hieroglyphs

def extract_alternative_forms(section_text):
    """Extract alternative forms from egy-hieroforms templates."""
    forms = []
    hieroforms_matches = re.findall(r'{{egy-hieroforms\|([^}]+)}}', section_text)
    for match in hieroforms_matches:
        params = match.split('|')
        for param in params:
            if param.strip().startswith('read'):
                form = re.sub(r'read\d*=', '', param).strip()
                if form and form not in forms:
                    forms.append(form)
    return forms

def parse_egyptian_section(wikitext, title):
    """Parse the wikitext to extract structured data using regex."""
    lemma_data = {
        "title": title,
        "part_of_speech": [],
        "definitions": [],
        "etymology": [],
        "usage_notes": "",
        "alternative_forms": [],
        "hieroglyphs": []
    }

    # Split wikitext into sections based on headers (=== or ====)
    sections = re.split(r'(===+[^=]+===+\n)', wikitext)
    current_etymology = None
    pos_sections = [
        "noun", "verb", "particle", "symbol", "pronoun", "preposition",
        "adjective", "adverb", "conjunction", "determiner", "interjection",
        "proper noun"
    ]

    i = 0
    while i < len(sections):
        if re.match(r'===+[^=]+===+', sections[i]):
            header = sections[i].strip('=\n').lower()
            content = sections[i + 1] if i + 1 < len(sections) else ""
            logging.debug(f"Processing section: {header}")

            # Check for etymology sections
            if header.startswith("etymology"):
                current_etymology = clean_text(content.split('====')[0])
                if current_etymology:
                    lemma_data["etymology"].append(current_etymology)
                    logging.debug(f"Extracted etymology: {current_etymology[:50]}...")
            
            # Check for part of speech sections
            elif header in pos_sections:
                lemma_data["part_of_speech"].append(header.capitalize())
                definitions = extract_definitions(content)
                lemma_data["definitions"].extend(definitions)
                logging.debug(f"Found {len(definitions)} definitions for {header}")
            
            # Check for usage notes
            elif header == "usage notes":
                usage_notes = clean_text(content)
                lemma_data["usage_notes"] = usage_notes
                logging.debug(f"Extracted usage notes: {usage_notes[:50]}...")
            
            # Check for alternative forms
            elif header == "alternative forms":
                forms = extract_alternative_forms(content)
                lemma_data["alternative_forms"].extend(forms)
                logging.debug(f"Extracted {len(forms)} alternative forms")
            
            # Extract hieroglyphs from all sections
            hieroglyphs = extract_hieroglyphs(content)
            lemma_data["hieroglyphs"].extend([h for h in hieroglyphs if h not in lemma_data["hieroglyphs"]])
        
        i += 2

    # Extract hieroglyphs from the entire wikitext (to catch any missed in sections)
    lemma_data["hieroglyphs"] = list(set(lemma_data["hieroglyphs"] + extract_hieroglyphs(wikitext)))
    logging.debug(f"Total hieroglyphs extracted: {len(lemma_data['hieroglyphs'])}")

    # Clean up empty fields
    lemma_data["etymology"] = [e for e in lemma_data["etymology"] if e]
    lemma_data["definitions"] = [d for d in lemma_data["definitions"] if d]
    lemma_data["alternative_forms"] = [f for f in lemma_data["alternative_forms"] if f]
    lemma_data["hieroglyphs"] = [h for h in lemma_data["hieroglyphs"] if h]

    # Log if no meaningful data was extracted
    if not any(lemma_data[key] for key in ["part_of_speech", "definitions", "etymology", "usage_notes", "alternative_forms", "hieroglyphs"]):
        logging.warning(f"No meaningful data extracted for {title}")

    return lemma_data

def save_parsed_data(data, output_file):
    """Save parsed data to a JSON file with atomic write."""
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".json") as temp_file:
        json.dump(data, temp_file, ensure_ascii=False, indent=2)
    
    try:
        os.replace(temp_file.name, output_file)
        logging.info(f"Saved parsed data to {output_file}")
    except Exception as e:
        logging.error(f"Error saving to {output_file}: {e}")
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)

def main():
    # Input data for testing
    test_data = {
        "ꜣ": {
            "egyptian_section": """{{also|Ꜣ}}
{{character info}}
==Translingual==

===Letter===
{{mul-letter|upper=Ꜣ|lower=ꜣ|script=Latn}}

# {{lb|mul|Egyptological transliteration}} The lowercase letter [[alef]], used in most Egyptian transliteration schemes to represent the sound of the hieroglyph [[𓄿|{{egy-h|A}}]].

===See also===
* {{l|mul|ʿ}}
* {{l|mul|3}}

==Egyptian==
[[File:Egyptian vulture.jpg|thumb|{{egy-h|A-Z1:H_SPACE}}]]

===Pronunciation===
{{egy-IPA-E}}

===Etymology 1===
Possibly from {{inh|egy|afa-pro|*ʔay-||bird of prey}}.<ref>{{R:HSED|*ʔay-}}</ref> Compare  also {{cog|sem-pro|*ʔayy-|t=bird of prey}}.

====Noun====
{{egy-noun|m|head=A}}

# the [[Egyptian vulture]] ({{taxfmt|Neophron percnopterus|species}}) {{defdate|Pyramid Texts and Coffin Texts}}
#* {{RQ:Pyramid Texts|P|V|S|||1|pt=539.1–539.2|pyr=1303a–1303b|v=V|quote={{egy-h|D-tp:Z1:n-<-ra:mr-i-i->-p:n-m-A-pr:r-f:r-f:S-Sw-w-i-i-f-r:f-i-r:p-t:pt}}
|tr=ḏd-(mdw) tp n(j) mry-rꜥ pn m '''ꜣ''' pr.f r.f šwy.f r.f jr pt
|t=Recitation (of words): The head of this Meryra is as a '''vulture''', so he should go forth, so he should soar up to the sky.}}
#* {{Q|egy||CT B1Bo|line 323–324, spell 677|refn=<ref>de Buck, Adriaan (1956) ''The Egyptian Coffin Texts'', volume VI, page 304 h–i</ref>|quote={{egy-h|s-Dr:r-A55-n-D-H-w&t-n:xt:x*t-p:n-m-wr:r-A40-p:f-x:r-A15:Hr-gs:Z1:f-!-wr:r-S:N8-f-A-i-s-<!--324-->snD-w-s-sxm-x-m-m-tp:p-t:f-A40}}
|tr=sḏr.n ḏḥwt(j)-nḫt pn m wr pf ḫr ḥr gs.f wrš.f '''ꜣ''' j.snḏw sḫm m tpt.f
|t=Djehutinakht has spent the night as yonder Great One who fell on his side, he passes the day as the '''vulture''' which is feared, being mighty by means of what is on him (i.e. his protective amulets).|transauthor=Faulkner<ref>Faulkner, Raymond (1977) ''The Ancient Egyptian Coffin Texts'', volume 2, page 244</ref>}}
# a [[bird]] in general {{defdate|11th Dynasty}}
#* {{c.|2061–2010 {{BCE}}}}, [[:File:Louvre stele chef artisans.JPG|Stela of Irtisen (Louvre C14)]], lines 9–10:
#*: {{quote|egy|{{egy-h|i-w-r:x:Y1-k:w-Sm:t-t:w-H_SPACE:t-A53-D54:t:Z1-B24-a:xrp:a-[sic]-w-nw:Z1-A-Z1:H_SPACE-mD:Z1}}
|tr=jw(.j) rḫ.kw šmt twt nmtt rpwt ꜥḥꜥw nw '''ꜣ''' mḏw-wꜥ
|I know the gait of a male figure, the stride of a female figure, and the stances of the eleven '''birds'''.}}

=====Inflection=====
{{egy-decl-noun|g=m
|ꜣ|hiero1=A
|hiero2=A-Z7:Z4
|hiero3=A-w-Z3}}

=====Alternative forms=====
{{egy-hieroforms
|A-Z1:H_SPACE|read1=ꜣ}}

===Etymology 2===

====Particle====
{{egy-part|enclitic|head=A}}

# {{ng|[[intensifying]] or [[emphasizing]] particle}}, [[indeed]] {{defdate|Pyramid Texts to New Kingdom and Greco-Roman Period}}
# {{lb|egy|in clauses with a verbal predicate in the perfect}} {{ng|marks a statement as [[hypothetical]] or [[contrafactual]]}}
# {{lb|egy|Neo-Middle Egyptian}} [[also]], [[and]] {{defdate|Greco-Roman Period}}

=====Usage notes=====
This particle is enclitic; it follows the word which it is intensifying or marking as contrafactual. It can also apply its effect to whole phrases. Often the exact nuance imparted by this particle is unclear.

Frequently this particle is found following (and thus adding emphasis to) {{m|egy|jsṯ|jsk}}, {{m|egy|ḥwj}}, {{m|egy|m}}{{m|egy|.k}}, or {{m|egy|ḥꜣ}}, and in the Pyramid Texts it is also found in nominal sentences preceding {{m|egy|pw}}. In Neo-Middle Egyptian it precedes rather than follows {{m|egy|jsṯ|(j)sk}} and {{m|egy|js}} but is often found following {{m|egy|jw}}.

=====Alternative forms=====
{{egy-hieroforms|title=Neo-Middle Egyptian hieroglyphic writings from Edfu that may also represent {{m|egy|yꜣ}}
|y:A|read1=jꜣ|date1=Greco-Roman Period
|A-W:H_SPACE|read2=ꜣw|date2=Greco-Roman Period
|A-y:W|read3=ꜣjw|date3=Greco-Roman Period
|G66-W:y|read4=ꜣwj|date4=Greco-Roman Period
|A-y:H_SPACE|read5=ꜣj|date5=Greco-Roman Period}}

=====Derived terms=====
{{col|egy
|nfr ꜣ
|ḥꜣ
|ḥꜣ ꜣ
|ḥwj ꜣ}}

=====Descendants=====
* {{desc|egy-lat|yꜣ|unc=1}} {{see desc}}

===Etymology 3===
Possibly from {{inh|egy|afa-pro|*ʔa-||to walk, to go}}.<ref>{{R:HSED|*ʔa-}}</ref>

====Verb====
{{egy-verb|head=A-D56}}

# {{lb|egy|intransitive|with {{m|egy|n}}}} to [[enter]] or [[tread]] (a place){{sup|?}} {{defdate|from Papyrus Westcar}}
# {{lb|egy|intransitive|of feet}} to [[tread]] {{defdate|Greco-Roman period}}

=====Usage notes=====
Gardiner considers the proper interpretation of this word “impossible in the lack of better evidence”. It is a [[dis legomenon]], with only two certain attested occurrences (but possibly up to four in total).

=====Alternative forms=====
{{egy-hieroforms
|A-D56|read1=ꜣ|date1=Second Intermediate Period?|note1=from Papyrus Westcar 9.16
|A-D54:H_SPACE|read2=ꜣ|date2=Greco-Roman Period}}

===Etymology 4===

====Verb====
{{egy-verb|head=A-D56-N23-Z1}}

# {{only used in|egy|jrj ꜣ r gs}}; {{ng|possibly a variant of the verb ‘to tread’ above.}} {{defdate|from Papyrus Westcar}}

===See also===
* {{l|egy|𓄿}}

===References===
* {{R:egy:Allen|196, 234|16.7, 18.8}}
* {{R:egy:Wb|1|1.1–1.10}}
* {{R:egy:Faulkner|1}}
* Gardiner, Alan (1948) “The First Two Pages of the ''Wörterbuch''” in ''The Journal of Egyptian Archaeology'', Vol. 34, p. 12–13
* {{R:egy:Gardiner|184|245}}
* {{R:egy:Meeks 2010|1–2}}
* {{R:egy:Wilson|1–2}}
* {{R:egy:HDECT|1}}
<references/>

{{C|egy|Birds}}
"""
        }
    }

    output_file = "test_parsed_egyptian_lemma.json"
    parsed_data = {}
    title = "ꜣ"
    
    logging.info(f"Processing test lemma: {title}")
    
    # Parse the Egyptian section
    wikitext = test_data[title]["egyptian_section"]
    lemma_data = parse_egyptian_section(wikitext, title)
    parsed_data[title] = lemma_data
    
    # Save the parsed data
    save_parsed_data(parsed_data, output_file)
    print(f"Done! Parsed test lemma {title}. Data saved to {output_file}")
    logging.info(f"Done! Parsed test lemma {title}. Data saved to {output_file}")

if __name__ == "__main__":
    main()
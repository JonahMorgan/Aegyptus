#!/usr/bin/env python3
"""Simple scraper for coptic-dictionary.org single-entry extraction.

Usage: python scrape_coptic_dictionary.py C37

This script is intentionally conservative: it fetches one entry, sleeps briefly, and
prints a JSON object with some structured fields (title, lemmas, refs, bibliography,
examples, full_text). It's meant as a lightweight test for one-off extraction.
"""
from __future__ import annotations

import argparse
import json
import re
import time
from typing import List, Dict

try:
    import requests
    from bs4 import BeautifulSoup
except Exception as e:  # pragma: no cover - best-effort import fallback
    raise SystemExit("This script requires 'requests' and 'beautifulsoup4'. Install them in your venv: pip install requests beautifulsoup4 lxml")

BASE = "https://coptic-dictionary.org/entry.cgi"
HEADERS = {"User-Agent": "Aegyptus-Data-scraper/1.0 (mailto:you@example.com)"}


def fetch_entry(tla: str, timeout: int = 30) -> str:
    resp = requests.get(BASE, params={"tla": tla}, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def extract_lemmas_from_tables(soup: BeautifulSoup) -> List[List[str]]:
    # heuristics: collect rows from tables that contain Coptic characters
    coptic_re = re.compile(r"[\u2C80-\u2CFF]")
    lemmas: List[List[str]] = []
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            cells = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
            if any(coptic_re.search(c) for c in cells if c):
                # keep cell texts (may include tla, tags, glosses)
                lemmas.append(cells)
    return lemmas


def parse_entry(html: str, tla: str) -> Dict:
    soup = BeautifulSoup(html, "lxml")

    # Title heuristics
    title_tag = soup.find(lambda t: t.name in ("h1", "h2", "h3") and "TLA lemma" in (t.get_text() or ""))
    if not title_tag:
        title_tag = soup.find("h2") or soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else None

    # Main content container heuristics
    content = soup.find(id="content") or soup.find("main") or soup.body or soup
    full_text = content.get_text("\n", strip=True)
    lines = [ln.strip() for ln in full_text.split("\n") if ln.strip()]

    # refs: lines containing 'ref:' (common on these pages)
    refs: List[str] = []
    bibliography: List[str] = []
    examples: List[str] = []
    for line in lines:
        lower = line.lower()
        if "ref:" in lower:
            # capture after 'ref:' up to 'bibliography:' if present
            after = line.split("ref:", 1)[1].strip()
            after = after.split("Bibliography:")[0].strip()
            refs.append(after)
        if "bibliography:" in lower:
            bibliography.append(line.split("Bibliography:", 1)[1].strip())
        if line.startswith("•") or line.startswith("-"):
            examples.append(line)

    lemmas = extract_lemmas_from_tables(soup)

    out = {
        "tla": tla,
        "title": title,
        "lemmas_table_rows": lemmas,
        "refs": refs,
        "bibliography": bibliography,
        "examples": examples,
        "full_text": full_text,
        "retrieved_from": BASE + "?tla=" + tla,
    }
    return out


def parse_entry_dom(html: str, tla: str) -> Dict:
    """Parse the HTML DOM to extract structured fields with improved regex.
    
    Strategy:
    1. Use full text to extract lemmas, senses, etymology, examples
    2. Use line-based parsing to handle newline-separated language tags
    """
    soup = BeautifulSoup(html, "lxml")
    result: Dict = {"tla": tla, "title": None, "lemmas": [], "senses": [], "etymology": {}, "examples": [], "see_also": {}, "refs": []}

    # title
    title_tag = soup.find(lambda t: t.name in ("h1", "h2", "h3") and "TLA lemma" in (t.get_text() or ""))
    if not title_tag:
        title_tag = soup.find("h2") or soup.find("h1")
    result["title"] = title_tag.get_text(strip=True) if title_tag else None

    # Get full text for parsing
    full_text = soup.get_text("\n")
    
    # Extract lemmas - forms are on separate lines from dialect/form_id
    # Structure:
    # ⲁⲗⲉ (line N)
    # S (line N+1 - dialect)
    # CF138 (line N+2 - form ID)
    # Vb. (line N+3 - POS)
    lemmas_seen = set()
    lines_list = full_text.split("\n")
    i = 0
    while i < len(lines_list):
        line = lines_list[i].strip()
        # Look for Coptic form at start of line
        if re.match(r"^[\u2C80-\u2CFF][\u2C80-\u2CFF\s⸗]*$", line):
            form = line
            # Peek ahead for dialect, form_id, pos
            dialect = None
            form_id = None
            pos = None
            if i + 1 < len(lines_list):
                next_line = lines_list[i + 1].strip()
                if next_line in ("S", "F", "B"):
                    dialect = next_line
                    if i + 2 < len(lines_list):
                        cf_line = lines_list[i + 2].strip()
                        if cf_line.startswith("CF"):
                            form_id = cf_line
                            if i + 3 < len(lines_list):
                                pos_line = lines_list[i + 3].strip()
                                if pos_line.startswith("Vb") or pos_line.startswith("N"):
                                    pos = pos_line
            
            if form not in lemmas_seen and dialect and form_id:
                lemmas_seen.add(form)
                entry = {"Form": form, "Dialect": dialect, "Form ID": form_id}
                if pos:
                    entry["POS"] = pos
                result["lemmas"].append(entry)
        i += 1

    # Parse senses more carefully
    # Senses appear AFTER lemma table but BEFORE "Descended from" section
    # Senses have structure:
    # \n(\d+).\n(En)\nTEXT\n(Fr)\nTEXT\n(De)\nTEXT\nBibliography:|ref:
    senses = []
    
    # Find the section bounds: from end of lemmas to "Descended from"
    etym_start = full_text.lower().find("descended from")
    senses_start = full_text.find("Scriptorium tag:")  # After all the ANNIS data
    if senses_start < 0:
        # Try alternative: after "Lemma frequency per 10,000"
        last_annis = full_text.rfind("Lemma frequency per 10,000")
        if last_annis > 0:
            senses_start = last_annis + 100  # Rough skip
    
    if senses_start > 0 and etym_start > senses_start:
        senses_text = full_text[senses_start:etym_start]
        
        # Parse sense entries: lines starting with digit
        i = 0
        lines_list = senses_text.split("\n")
        for i, line in enumerate(lines_list):
            line_stripped = line.strip()
            # Look for sense number marker (e.g., "1.", "2.", "3.")
            if re.match(r"^\d+\.$", line_stripped) and len(line_stripped) <= 3:
                sense_id = line_stripped[:-1]
                en_text = None
                fr_text = None
                de_text = None
                
                # Scan ahead for (En), (Fr), (De) with next non-empty line as content
                j = i + 1
                while j < len(lines_list) and j < i + 20:  # Limit scan ahead
                    next_line = lines_list[j].strip()
                    if next_line == "(En)":
                        j += 1
                        while j < len(lines_list) and not lines_list[j].strip():
                            j += 1
                        if j < len(lines_list):
                            en_text = lines_list[j].strip()
                    elif next_line == "(Fr)":
                        j += 1
                        while j < len(lines_list) and not lines_list[j].strip():
                            j += 1
                        if j < len(lines_list):
                            fr_text = lines_list[j].strip()
                    elif next_line == "(De)":
                        j += 1
                        while j < len(lines_list) and not lines_list[j].strip():
                            j += 1
                        if j < len(lines_list):
                            de_text = lines_list[j].strip()
                    elif next_line and not next_line.startswith("(") and en_text and fr_text and de_text:
                        break
                    j += 1
                
                # Only add if we found translations
                if en_text or fr_text or de_text:
                    senses.append({"sense_id": sense_id, "en": en_text, "fr": fr_text, "de": de_text})

    result["senses"] = senses

    # Parse etymology section
    # Find "Descended from" block
    etym_match = re.search(
        r"Descended from\s+(.*?)(?:Example usage|See also|Please cite)",
        full_text,
        re.DOTALL | re.IGNORECASE
    )
    if etym_match:
        full_etym = etym_match.group(1).strip()
        
        # First, extract all WCN IDs from anywhere in the etymology
        wcn_all = {}
        for m in re.finditer(r"(WCN[a-z]+):\s*([A-Za-z0-9]+)", full_etym, re.I):
            key = m.group(1)
            val = m.group(2)
            wcn_all.setdefault(key, []).append(val)
        
        # Remove WCN lines for cleaner parsing
        etym_clean = re.sub(r"\s*WCN[a-z]+:\s*[A-Za-z0-9]+", "", full_etym, flags=re.I)
        
        # Split main etymology from "cf." section
        cf_split = re.split(r"\bcf\.\s+", etym_clean, maxsplit=1, flags=re.IGNORECASE)
        main_etym = cf_split[0].strip()
        cf_section = cf_split[1].strip() if len(cf_split) > 1 else None
        
        # Parse main etymology: "Demotic FORM, Hieroglyphic Egyptian FORM to DESCRIPTION"
        demotic_term = None
        hieroglyphic_term = None
        description = None
        
        # Extract Demotic term - appears after "Demotic" on next line(s)
        dem_match = re.search(r"Demotic\s+([^\n,]+)", main_etym)
        if dem_match:
            demotic_term = dem_match.group(1).strip()
        
        # Extract Hieroglyphic Egyptian term - appears after "Hieroglyphic Egyptian"
        hier_match = re.search(r"Hieroglyphic Egyptian\s+([^\n,]+?)(?:\s+to\s+|\s+[a-z])", main_etym)
        if hier_match:
            hieroglyphic_term = hier_match.group(1).strip()
        
        # Extract description: everything after the form terms and before "see TLA" 
        # Look for "to DESCRIPTION" part
        desc_match = re.search(r"\s+to\s+([^s][^\[]*?)(?:see TLA|\[|$)", main_etym)
        if desc_match:
            desc_text = desc_match.group(1).strip()
            description = " ".join(desc_text.split())
        
        # Parse cf. section if present
        cf_data = None
        if cf_section:
            cf_data = {"raw": cf_section}
            cf_terms = []
            
            # Split by additional "cf." markers within the cf section
            cf_parts = re.split(r"\bcf\.\s+", cf_section, flags=re.IGNORECASE)
            for part in cf_parts:
                part = part.strip()
                if not part:
                    continue
                # Extract first Coptic/Egyptian word and its gloss
                # Pattern: WORD(s) whitespace GLOSS
                m = re.match(r"^([\u2C80-\u2CFF\s⸗]+?)\s{2,}([^cf][^\n]*?)$", part, re.MULTILINE)
                if m:
                    term = m.group(1).strip()
                    gloss = m.group(2).strip()
                    cf_terms.append({"term": term, "gloss": gloss})
            
            if cf_terms:
                cf_data["terms"] = cf_terms
        
        # Structure the etymology output
        result["etymology"] = {
            "raw": full_etym,
            "main": {
                "demotic": demotic_term,
                "hieroglyphic": hieroglyphic_term,
                "description": description
            },
            "cf": cf_data,
            "wcn": wcn_all if wcn_all else None
        }

    # Examples with URNs
    ex_match = re.search(
        r"Example usage\s+(.*?)(?:See also|Please cite|$)",
        full_text,
        re.DOTALL | re.IGNORECASE
    )
    if ex_match:
        ex_text = ex_match.group(1)
        # Extract URNs
        urns = re.findall(r"(urn:[^\s\)]+)", ex_text)
        if urns or ex_text.strip():
            result["examples"].append({"text": ex_text.strip()[:200], "urns": urns})

    # See also: extract related TLA entries
    for m in re.finditer(r"entry\.(?:py|cgi)\?tla=([A-Z0-9]+)", full_text):
        tla_id = m.group(1)
        result["see_also"][tla_id] = f"entry.cgi?tla={tla_id}"

    return result


def main():
    p = argparse.ArgumentParser(description="Fetch and parse a single Coptic Dictionary TLA entry (test)")
    p.add_argument("tla", help="TLA id, e.g. C37")
    p.add_argument("--sleep", type=float, default=1.5, help="Seconds to sleep after fetch (politeness)")
    p.add_argument("--out", "-o", help="Output file path (writes JSON utf-8)")
    p.add_argument("--dom", action="store_true", help="Parse DOM and produce structured JSON instead of text heuristics")
    args = p.parse_args()
    html = fetch_entry(args.tla)
    # polite pause
    time.sleep(args.sleep)
    if args.dom:
        parsed = parse_entry_dom(html, args.tla)
    else:
        parsed = parse_entry(html, args.tla)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(parsed, fh, ensure_ascii=False, indent=2)
        print(f"Wrote: {args.out}")
    else:
        print(json.dumps(parsed, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

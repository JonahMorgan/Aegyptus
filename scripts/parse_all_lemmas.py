#!/usr/bin/env python3
"""Parse raw HTML data from all_lemmas.jsonl into structured format.

This script reads the raw HTML from all_lemmas.jsonl and extracts:
- lemmas (Coptic forms with dialect, form ID, POS)
- senses (numbered definitions with translations in En/Fr/De)
- etymology (demotic, hieroglyphic, cf. terms, WCN IDs)
- examples
- see_also references

Output:
    all_lemmas_parsed.jsonl         # Newline-delimited parsed entries
    all_lemmas_parsed.json          # JSON array of parsed entries
    parse_stats.json                # Parsing statistics
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

try:
    from bs4 import BeautifulSoup
except ImportError:
    raise SystemExit("This script requires 'beautifulsoup4'. Install: pip install beautifulsoup4 lxml")


def parse_entry_from_html(html: str, tla: str) -> Dict:
    """Parse HTML into structured dictionary format using the same method as c37_final.json."""
    soup = BeautifulSoup(html, "lxml")
    result: Dict = {
        "tla": tla,
        "title": None,
        "lemmas": [],
        "senses": [],
        "etymology": {},
        "examples": [],
        "see_also": {},
        "refs": [],
    }

    # Extract title
    title_tag = soup.find(lambda t: t.name in ("h1", "h2", "h3") and "TLA lemma" in (t.get_text() or ""))
    if not title_tag:
        title_tag = soup.find("h2") or soup.find("h1")
    result["title"] = title_tag.get_text(strip=True) if title_tag else None

    # Get full text for parsing
    full_text = soup.get_text("\n")

    # Extract lemmas from HTML table
    lemmas_seen = set()
    
    # Look for table with id="orths" or any table with Form/Dial./Form ID headers
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if not cells or len(cells) < 3:
                continue
            
            # Extract cell text content
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            
            # Skip header rows
            if any(header in cell_texts for header in ['Form', 'Dial.', 'POS']):
                continue
            
            # Look for rows with Coptic text in first cell
            if len(cell_texts) > 0 and re.search(r"[\u2C80-\u2CFF]", cell_texts[0]):
                form = cell_texts[0] if cell_texts[0] else None
                dialect = cell_texts[1] if len(cell_texts) > 1 else None
                form_id = cell_texts[2] if len(cell_texts) > 2 else None
                pos = cell_texts[3] if len(cell_texts) > 3 else None
                
                # Only add if we have at least form and dialect
                if form and dialect and form not in lemmas_seen:
                    lemmas_seen.add(form)
                    entry = {"Form": form, "Dialect": dialect, "Form ID": form_id}
                    if pos and pos.strip():
                        entry["POS"] = pos
                    result["lemmas"].append(entry)
    
    # Fallback: if no lemmas found, try to extract from title
    if not result["lemmas"] and result["title"]:
        title = result["title"]
        # Extract everything after the last space that contains Coptic characters
        m = re.search(r"\s([\u2C80-\u2CFF\s⸗]+)$", title)
        if m:
            form = m.group(1).strip()
            if form and re.search(r"[\u2C80-\u2CFF]", form):
                result["lemmas"].append({"Form": form, "Dialect": None, "Form ID": None})

    # Parse senses - more robust extraction
    senses = []
    
    # Find section boundaries
    etym_start_pos = full_text.lower().find("demotic")
    if etym_start_pos < 0:
        etym_start_pos = full_text.lower().find("hieroglyphic")
    if etym_start_pos < 0:
        etym_start_pos = full_text.lower().find("descended from")
    if etym_start_pos < 0:
        etym_start_pos = len(full_text)
    
    # Find section start (after lemmas table)
    senses_start = full_text.find("Lemma frequency")
    if senses_start < 0:
        senses_start = 0
    else:
        senses_start += 200  # Skip past frequency data
    
    # Extract senses block
    senses_text = full_text[senses_start:etym_start_pos]
    lines_list = senses_text.split("\n")
    
    # Look for numbered senses (1., 2., 3., etc.)
    i = 0
    while i < len(lines_list):
        line = lines_list[i].strip()
        # Match sense number at line start
        if re.match(r"^\d+\.\s*$", line):
            sense_id = line.rstrip(".")
            en_text = None
            fr_text = None
            de_text = None
            
            # Scan forward for language markers
            j = i + 1
            max_scan = min(i + 30, len(lines_list))
            while j < max_scan:
                next_line = lines_list[j].strip()
                
                if next_line == "(En)" or next_line.startswith("(En)"):
                    # Get translation after this marker
                    k = j + 1
                    while k < max_scan and not lines_list[k].strip():
                        k += 1
                    if k < max_scan:
                        en_text = lines_list[k].strip()
                
                elif next_line == "(Fr)" or next_line.startswith("(Fr)"):
                    k = j + 1
                    while k < max_scan and not lines_list[k].strip():
                        k += 1
                    if k < max_scan:
                        fr_text = lines_list[k].strip()
                
                elif next_line == "(De)" or next_line.startswith("(De)"):
                    k = j + 1
                    while k < max_scan and not lines_list[k].strip():
                        k += 1
                    if k < max_scan:
                        de_text = lines_list[k].strip()
                
                # Stop when we hit next sense or end marker
                if re.match(r"^\d+\.\s*$", next_line) and j > i + 2:
                    break
                if any(stop in next_line.lower() for stop in ['demotic', 'hieroglyphic', 'descended']):
                    break
                
                j += 1
            
            # Add sense if we found at least one translation
            if en_text or fr_text or de_text:
                senses.append({
                    "sense_id": sense_id,
                    "en": en_text,
                    "fr": fr_text,
                    "de": de_text
                })
        
        i += 1
    
    result["senses"] = senses

    # Parse etymology section - more robust extraction
    # Find where etymology section starts (look for "Demotic" or "Hieroglyphic" markers)
    lines = [ln.rstrip() for ln in full_text.splitlines()]
    ety_idx = None
    for i, ln in enumerate(lines):
        if any(marker in ln.lower() for marker in ['demotic', 'hieroglyphic', 'descended from']):
            ety_idx = i
            break
    
    if ety_idx is not None:
        # Collect etymology block (up to 50 lines from marker)
        block = []
        for ln in lines[ety_idx: min(ety_idx + 50, len(lines))]:
            if ln.strip() == "" and len(block) > 5:
                # Stop at significant blank line
                break
            if any(stop_marker in ln.lower() for stop_marker in ['example usage', 'see also', 'please cite', 'bibliography']):
                break
            block.append(ln)
        
        etym_text = "\n".join(block)
        
        if etym_text.strip():
            # Extract languages mentioned
            langs = re.findall(r"(Demotic|Hieroglyphic Egyptian|Hieroglyphic|Egyptian)", etym_text, flags=re.I)
            
            # Extract short forms (non-ASCII tokens or Egyptian unicode)
            tokens = re.findall(r"[\w\u0100-\uFFFF]+", etym_text)
            short_forms = [t for t in tokens if re.search(r"[^A-Za-z0-9]", t) or re.search(r"[\u2C80-\u2CFF]", t)]
            
            # Extract demotic and hieroglyphic terms
            demotic_term = None
            hieroglyphic_term = None
            description = None
            
            dem_match = re.search(r"Demotic\s+([^\n,;]+)", etym_text, re.I)
            if dem_match:
                demotic_term = dem_match.group(1).strip().rstrip('[]')
            
            hier_match = re.search(r"Hieroglyphic(?:\s+Egyptian)?\s+([^\n,;]+)", etym_text, re.I)
            if hier_match:
                hieroglyphic_term = hier_match.group(1).strip().rstrip('[]')
            
            # Try to find description (usually "X meaning" or similar)
            desc_patterns = [
                r'(?:meaning|translated as|= |,\s*)([^;\[]*?)(?:;|\[|(?:Demotic|Hieroglyphic)|$)',
            ]
            for pattern in desc_patterns:
                desc_match = re.search(pattern, etym_text, re.I)
                if desc_match:
                    desc = desc_match.group(1).strip()
                    if desc and len(desc) > 2 and not any(x in desc for x in ['Demotic', 'Hieroglyphic']):
                        description = desc
                        break
            
            # Parse cf. section
            cf_data = None
            cf_match = re.search(r"cf\.\s*(.*?)(?:;|\n\n|Example|$)", etym_text, re.I | re.S)
            if cf_match:
                cf_raw = cf_match.group(1).strip()
                cf_data = {"raw": cf_raw}
                # Try to extract individual cf terms
                cf_terms = []
                for cf_term_match in re.finditer(r"([\u2C80-\u2CFF\s⸗]+?)\s+([^,;\n]+)", cf_raw):
                    term = cf_term_match.group(1).strip()
                    gloss = cf_term_match.group(2).strip()
                    if term and gloss:
                        cf_terms.append({"term": term, "gloss": gloss})
                if cf_terms:
                    cf_data["terms"] = cf_terms
            
            # Extract WCN IDs
            wcn_all = {}
            for m in re.finditer(r"(WCN\w*):\s*([A-Za-z0-9]+)", etym_text, re.I):
                key = m.group(1)
                val = m.group(2)
                wcn_all.setdefault(key, []).append(val)
            
            result["etymology"] = {
                "raw": etym_text,
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


def parse_all_lemmas(input_file: Path, output_jsonl: Path, output_json: Path, stats_file: Path):
    """Parse all raw HTML entries from JSONL file."""
    parsed_entries = []
    stats = {
        "total_entries": 0,
        "successful": 0,
        "failed": 0,
        "with_lemmas": 0,
        "with_senses": 0,
        "with_etymology": 0,
    }

    print(f"Parsing {input_file}...")

    with open(input_file, "r", encoding="utf-8") as f_in, open(output_jsonl, "w", encoding="utf-8") as f_out:
        for line_num, line in enumerate(f_in, 1):
            if not line.strip():
                continue

            try:
                raw_entry = json.loads(line)
                tla = raw_entry.get("tla")
                html = raw_entry.get("html")

                if not tla or not html:
                    stats["failed"] += 1
                    continue

                # Parse the HTML
                parsed = parse_entry_from_html(html, tla)
                parsed_entries.append(parsed)

                # Write to JSONL
                f_out.write(json.dumps(parsed, ensure_ascii=False) + "\n")

                # Update stats
                stats["total_entries"] += 1
                stats["successful"] += 1
                if parsed.get("lemmas"):
                    stats["with_lemmas"] += 1
                if parsed.get("senses"):
                    stats["with_senses"] += 1
                if parsed.get("etymology"):
                    stats["with_etymology"] += 1

                if line_num % 10 == 0:
                    print(f"  Processed {line_num} entries...", end="\r")

            except json.JSONDecodeError as e:
                stats["failed"] += 1
                print(f"\nError parsing line {line_num}: {e}")
            except Exception as e:
                stats["failed"] += 1
                print(f"\nError processing entry at line {line_num}: {e}")

    # Write JSON array
    print(f"\n\nWriting {output_json}...")
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(parsed_entries, f, ensure_ascii=False, indent=2)

    # Write stats
    print(f"Writing {stats_file}...")
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    # Print summary
    print(f"\n{'='*60}")
    print(f"PARSING SUMMARY")
    print(f"{'='*60}")
    print(f"Total entries:      {stats['total_entries']}")
    print(f"Successful:         {stats['successful']}")
    print(f"Failed:             {stats['failed']}")
    print(f"With lemmas:        {stats['with_lemmas']}")
    print(f"With senses:        {stats['with_senses']}")
    print(f"With etymology:     {stats['with_etymology']}")
    print(f"{'='*60}")
    print(f"Output:")
    print(f"  JSONL:   {output_jsonl}")
    print(f"  JSON:    {output_json}")
    print(f"  Stats:   {stats_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Parse raw HTML data from all_lemmas.jsonl into structured format.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).parent / "all_lemmas.jsonl",
        help="Input JSONL file with raw HTML (default: all_lemmas.jsonl)",
    )
    parser.add_argument(
        "--output-jsonl",
        type=Path,
        default=Path(__file__).parent / "all_lemmas_parsed.jsonl",
        help="Output JSONL file (default: all_lemmas_parsed.jsonl)",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path(__file__).parent / "all_lemmas_parsed.json",
        help="Output JSON file (default: all_lemmas_parsed.json)",
    )
    parser.add_argument(
        "--stats",
        type=Path,
        default=Path(__file__).parent / "parse_stats.json",
        help="Statistics output file (default: parse_stats.json)",
    )

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        return 1

    parse_all_lemmas(args.input, args.output_jsonl, args.output_json, args.stats)
    return 0


if __name__ == "__main__":
    exit(main())

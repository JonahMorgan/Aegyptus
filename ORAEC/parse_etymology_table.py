#!/usr/bin/env python3
"""Parse the etymology table in ORAEC.htm and export rows as JSON/JSONL.

Outputs:
 - oraec_etymologies.jsonl (one JSON object per row)
 - oraec_etymologies.json (array of rows)

Each row is a dict with keys: coptic, egyptian, demotic. Each value is an object with:
 - text: plain text content
 - html: inner HTML of the cell (trimmed)
 - links: list of link hrefs found in the cell

Usage: python parse_etymology_table.py /path/to/ORAEC.htm
If no path provided, defaults to ./ORAEC.htm next to this script.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

try:
    from bs4 import BeautifulSoup
except Exception as e:
    raise SystemExit(
        "BeautifulSoup is required. Install with: pip install beautifulsoup4 lxml"
    )


def extract_cell(cell) -> Dict[str, Any]:
    """Return a compact representation for a table cell.

    Output keys (only included if non-empty):
      - lemma: plain text content of the cell
      - link: first href found in the cell (if any)
    """
    if cell is None:
        return {}
    # plain text (replace NBSP with regular space)
    text = cell.get_text(" ", strip=True).replace('\xa0', ' ')
    # first link href, if present
    first_href = None
    a = cell.find("a", href=True)
    if a:
        first_href = a["href"]

    result: Dict[str, Any] = {}
    if text:
        result["lemma"] = text
    if first_href:
        result["link"] = first_href
    return result


def find_etymology_table(soup: BeautifulSoup):
    # look for table whose header contains Coptic, Egyptian, Demotic (case-insensitive)
    for table in soup.find_all("table"):
        # find header cells
        headers = [h.get_text(" ", strip=True).lower() for h in table.find_all(["th"])][:5]
        if not headers:
            # perhaps first row has the headers as <td>
            first_row = table.find("tr")
            if first_row:
                headers = [td.get_text(" ", strip=True).lower() for td in first_row.find_all(["td"])][:5]
        if headers:
            joined = "|".join(headers)
            if "coptic" in joined and "egyptian" in joined and "demotic" in joined:
                return table
    return None


def parse_table(table) -> List[Dict[str, Any]]:
    rows = []
    # prefer tbody/tr, but fallback to direct tr children
    tr_list = table.find_all("tr")
    # skip header row(s) -- find first row that contains the header labels
    start_idx = 0
    for i, tr in enumerate(tr_list[:5]):
        texts = [c.get_text(" ", strip=True).lower() for c in tr.find_all(["th", "td"]) ]
        joined = "|".join(texts)
        if "coptic" in joined and "egyptian" in joined and "demotic" in joined:
            start_idx = i + 1
            break

    for tr in tr_list[start_idx:]:
        # skip entirely empty rows
        if not tr.find_all(["td", "th"]):
            continue
        tds = tr.find_all(["td", "th"])
        # ensure we have at least 3 columns
        # sometimes there are rows with 1 cell (spacer) - skip them
        if len(tds) < 1:
            continue
        # map first three cells to columns; if fewer, pad with None
        cells = []
        for i in range(3):
            cells.append(tds[i] if i < len(tds) else None)

        # extract cells but only include non-empty fields
        record: Dict[str, Any] = {}
        cols = ["coptic", "egyptian", "demotic"]
        for name, cell in zip(cols, cells):
            value = extract_cell(cell)
            # consider a cell non-empty if it has lemma or link
            if value.get("lemma") or value.get("link"):
                record[name] = value
        # skip rows that are all empty
        if not record:
            continue
        rows.append(record)
    return rows


def main(argv: List[str]):
    if len(argv) > 1:
        path = Path(argv[1])
    else:
        path = Path(__file__).parent / "ORAEC.htm"

    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(2)

    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")

    table = find_etymology_table(soup)
    if table is None:
        print("Could not find the etymology table (headers Coptic/Egyptian/Demotic).")
        sys.exit(3)

    rows = parse_table(table)
    out_dir = Path(__file__).parent
    jsonl_path = out_dir / "oraec_etymologies.jsonl"
    json_path = out_dir / "oraec_etymologies.json"

    with jsonl_path.open("w", encoding="utf-8") as jl:
        for r in rows:
            jl.write(json.dumps(r, ensure_ascii=False) + "\n")

    with json_path.open("w", encoding="utf-8") as j:
        json.dump(rows, j, ensure_ascii=False, indent=2)

    print(f"Wrote {len(rows)} rows to:\n - {jsonl_path}\n - {json_path}")


if __name__ == "__main__":
    main(sys.argv)

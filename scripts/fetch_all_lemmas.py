#!/usr/bin/env python3
"""Bulk lemma fetcher for coptic-dictionary.org with polite rate-limiting.

This script discovers and fetches all available Coptic lemmas from the online
dictionary, saving raw HTML data without parsing. Respects server resources with 
configurable delays and caching.

Usage:
    python fetch_all_lemmas.py                    # Fetch all lemmas with defaults
    python fetch_all_lemmas.py --start C1 --end C5000  # Fetch range
    python fetch_all_lemmas.py --sleep 2.0 --max 100   # Custom delay and max count
    python fetch_all_lemmas.py --skip-cache           # Ignore cache and refetch everything

Output:
    all_lemmas.jsonl              # Newline-delimited JSON with raw HTML (streaming format)
    all_lemmas.json               # JSON array (summary format)
    lemma_fetch_log.txt           # Detailed log with timestamps and errors
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    raise SystemExit("This script requires 'requests' and 'beautifulsoup4'. Install: pip install requests beautifulsoup4 lxml")

BASE = "https://coptic-dictionary.org/entry.cgi"
HEADERS = {"User-Agent": "Aegyptus-Data-scraper/1.0 (Aegyptus project. For personal use only); mailto:jonah.morgan@tcu.edu)"}


def fetch_entry(tla: str, timeout: int = 10) -> Optional[str]:
    """Fetch a single entry HTML from coptic-dictionary.org (no retries, fast fail)."""
    try:
        resp = requests.get(BASE, params={"tla": tla}, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.RequestException:
        return None


def save_raw_entry(html: str, tla: str) -> Dict:
    """Save raw HTML data without parsing."""
    return {
        "tla": tla,
        "html": html,
        "fetched_at": datetime.now().isoformat(),
    }


def get_tla_range(start: Optional[str] = None, end: Optional[str] = None) -> tuple[int, int]:
    """Parse TLA range (e.g., 'C1' -> 1, 'C5000' -> 5000)."""
    start_num = int(start.lstrip("C")) if start else 1
    end_num = int(end.lstrip("C")) if end else 9999
    return start_num, end_num


def load_cache(cache_file: Path) -> set[str]:
    """Load set of already-fetched TLA IDs from cache."""
    if cache_file.exists():
        try:
            with open(cache_file, "r") as f:
                return set(line.split("\t")[0] for line in f if line.strip())
        except Exception:
            pass
    return set()


def save_result(result: Dict, jsonl_file: Path, json_file: Path, log_file: Path, log_msg: str = ""):
    """Append result to JSONL, update JSON array, and log."""
    # Write to JSONL (append mode)
    with open(jsonl_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")

    # Log
    timestamp = datetime.now().isoformat()
    status = "✓" if result.get("title") else "✗"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {status} {result['tla']}: {log_msg}\n")


def load_jsonl(jsonl_file: Path) -> List[Dict]:
    """Load all results from JSONL file."""
    results = []
    if jsonl_file.exists():
        try:
            with open(jsonl_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        results.append(json.loads(line))
        except Exception:
            pass
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Bulk fetch all Coptic lemmas from coptic-dictionary.org with rate-limiting.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fetch_all_lemmas.py                      # Fetch all (default C1-C9999)
  python fetch_all_lemmas.py --start C1 --end C100  # Fetch range C1-C100
  python fetch_all_lemmas.py --sleep 1.5 --max 50  # 1.5s delay, max 50 entries
  python fetch_all_lemmas.py --skip-cache         # Refetch all (ignore cache)
        """,
    )
    parser.add_argument("--start", default="C1", help="Starting TLA ID (default: C1)")
    parser.add_argument("--end", default="C9999", help="Ending TLA ID (default: C9999)")
    parser.add_argument("--sleep", type=float, default=0.5, help="Delay between requests in seconds (default: 0.5)")
    parser.add_argument("--max", type=int, default=None, help="Max lemmas to fetch (default: no limit)")
    parser.add_argument("--skip-cache", action="store_true", help="Ignore cache and refetch all")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent, help="Output directory (default: script directory)")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    jsonl_file = output_dir / "all_lemmas.jsonl"
    json_file = output_dir / "all_lemmas.json"
    log_file = output_dir / "lemma_fetch_log.txt"
    cache_file = output_dir / "lemma_cache.tsv"

    # Load existing cache or start fresh
    cached = load_cache(cache_file) if not args.skip_cache else set()
    start_num, end_num = get_tla_range(args.start, args.end)

    print(f"Fetching Coptic lemmas C{start_num}–C{end_num}")
    print(f"  Sleep delay: {args.sleep}s between requests")
    if args.max:
        print(f"  Max lemmas: {args.max}")
    print(f"  Cache: {len(cached)} already fetched")
    print(f"  Output: {output_dir}")
    print()

    fetched_count = 0
    error_count = 0
    skipped_count = 0
    
    # Buffers for batch writing (reduces I/O overhead)
    jsonl_buffer = []
    cache_buffer = []
    BUFFER_SIZE = 50  # Write every 50 entries

    for num in range(start_num, end_num + 1):
        tla = f"C{num}"

        # Check cache
        if tla in cached and not args.skip_cache:
            skipped_count += 1
            continue

        # Check max limit
        if args.max and fetched_count >= args.max:
            print(f"\nReached max limit ({args.max}), stopping.")
            break

        # Fetch
        print(f"Fetching {tla}...", end=" ", flush=True)
        html = fetch_entry(tla)

        if html:
            # Save raw HTML without parsing
            result = save_raw_entry(html, tla)
            jsonl_buffer.append(json.dumps(result, ensure_ascii=False))
            cache_buffer.append(f"{tla}\t{datetime.now().isoformat()}\n")
            fetched_count += 1
            print(f"✓ ({len(html)} bytes)")
        else:
            error_count += 1
            print("✗ (fetch failed)")

        # Rate limit
        time.sleep(args.sleep)
        
        # Flush buffers periodically
        if len(jsonl_buffer) >= BUFFER_SIZE:
            with open(jsonl_file, "a", encoding="utf-8") as f:
                f.write("\n".join(jsonl_buffer) + "\n")
            with open(cache_file, "a", encoding="utf-8") as f:
                f.writelines(cache_buffer)
            jsonl_buffer = []
            cache_buffer = []
        
        # Progress update every 100 entries
        if (fetched_count + skipped_count) % 100 == 0:
            print(f"  [Progress: {fetched_count} fetched, {skipped_count} skipped, {error_count} errors]", flush=True)

    # Flush any remaining buffers
    if jsonl_buffer:
        with open(jsonl_file, "a", encoding="utf-8") as f:
            f.write("\n".join(jsonl_buffer) + "\n")
    if cache_buffer:
        with open(cache_file, "a", encoding="utf-8") as f:
            f.writelines(cache_buffer)

    # Print summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Fetched:   {fetched_count}")
    print(f"Errors:    {error_count}")
    print(f"Skipped:   {skipped_count} (from cache)")
    print(f"Output:    {jsonl_file}")
    print(f"Cache:     {cache_file}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

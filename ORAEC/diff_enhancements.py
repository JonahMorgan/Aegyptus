"""Diff enhanced etymology data against the original complete dataset.

Usage (PowerShell):
  python diff_enhancements.py [--limit 15] [--fields coptic_word,egyptian_word,demotic_word]

By default it:
  * Loads coptic_etymologies_complete.json (original)
  * Loads coptic_etymologies_enhanced.json (after table merge)
  * Compares selected fields (added / changed)
  * Prints summary counts and sample differences

Exit codes:
  0 success
  1 file missing / error
"""
from __future__ import annotations
import json, argparse, sys, pathlib

ORAEC_DIR = pathlib.Path(r"c:\Users\user\Desktop\Aegyptus Transformer\Aegyptus Data\ORAEC")
ORIGINAL = ORAEC_DIR / "coptic_etymologies_complete.json"
ENHANCED = ORAEC_DIR / "coptic_etymologies_enhanced.json"

DEFAULT_FIELDS = ["coptic_word", "egyptian_word", "demotic_word"]

def load(path: pathlib.Path):
    if not path.exists():
        print(f"ERROR: Missing file: {path}")
        sys.exit(1)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def index_by_id(data):
    return {e["coptic_id"]: e for e in data if "coptic_id" in e}

def diff(original, enhanced, fields):
    diffs = []
    for cid, orig_entry in original.items():
        enh_entry = enhanced.get(cid)
        if not enh_entry:
            continue
        field_changes = {}
        for field in fields:
            o_val = orig_entry.get(field)
            e_val = enh_entry.get(field)
            if o_val != e_val:
                # classify change
                change_type = (
                    "added" if o_val in (None, "") and e_val not in (None, "") else
                    "removed" if e_val in (None, "") and o_val not in (None, "") else
                    "modified"
                )
                field_changes[field] = {
                    "original": o_val,
                    "enhanced": e_val,
                    "change": change_type
                }
        if field_changes:
            diffs.append({"coptic_id": cid, **field_changes})
    return diffs

def summarize(diffs, fields):
    summary = {f: {"added": 0, "removed": 0, "modified": 0} for f in fields}
    for d in diffs:
        for f in fields:
            if f in d:
                summary[f][d[f]["change"]] += 1
    return summary

def format_change(ch):
    o = ch["original"] if ch["original"] is not None else "∅"
    e = ch["enhanced"] if ch["enhanced"] is not None else "∅"
    return f"{ch['change']}: {o} → {e}"

def main(argv=None):
    parser = argparse.ArgumentParser(description="Diff original vs enhanced etymology dataset")
    parser.add_argument("--limit", type=int, default=10, help="Max sample differences to print")
    parser.add_argument("--fields", type=str, default=",".join(DEFAULT_FIELDS), help="Comma-separated list of fields to compare")
    args = parser.parse_args(argv)
    fields = [f.strip() for f in args.fields.split(",") if f.strip()]

    orig_data = load(ORIGINAL)
    enh_data = load(ENHANCED)
    orig_index = index_by_id(orig_data)
    enh_index = index_by_id(enh_data)

    diffs = diff(orig_index, enh_index, fields)
    summary = summarize(diffs, fields)

    print("=" * 60)
    print("ENHANCEMENT DIFF SUMMARY")
    print("=" * 60)
    print(f"Total entries compared: {len(orig_index)}")
    print(f"Entries with any change in target fields: {len(diffs)} ({len(diffs)/len(orig_index)*100:.1f}%)")
    print()
    for f in fields:
        s = summary[f]
        total_f = s["added"] + s["removed"] + s["modified"]
        print(f"Field '{f}': {total_f} changes (added={s['added']}, removed={s['removed']}, modified={s['modified']})")
    print()

    print("Sample differences (limit = {}):".format(args.limit))
    for entry in diffs[: args.limit]:
        cid = entry["coptic_id"]
        changes_rendered = [f"{fld}: {format_change(entry[fld])}" for fld in fields if fld in entry]
        print(f" - {cid}: " + "; ".join(changes_rendered))

    print("\nDone.")

if __name__ == "__main__":
    main()

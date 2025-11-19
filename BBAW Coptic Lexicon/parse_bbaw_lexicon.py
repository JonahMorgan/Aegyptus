#!/usr/bin/env python3
"""Parse the BBAW TEI lexicon XML and extract entries to JSON/JSONL.

Outputs:
 - bbaw_lexicon.jsonl (one JSON object per entry)
 - bbaw_lexicon.json (array of entries)

Extraction policy (compact, omits empty subfields):
 - id: entry xml:id
 - type: entry @type (if present)
 - forms: list of { id, type, orth, usg: [..], gram: { pos, subc, note } }
 - senses: list of { id, translations: {lang: text}, bibl: text (if any) }

Usage: python parse_bbaw_lexicon.py [path/to/BBAW_Lexicon_of_Coptic_Egyptian-v4-2020.xml]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

from lxml import etree


NS = {"tei": "http://www.tei-c.org/ns/1.0"}


def xml_id(elem: etree._Element) -> Optional[str]:
    # xml:id is in the XML namespace
    xml_ns = "{http://www.w3.org/XML/1998/namespace}id"
    return elem.get(xml_ns) or elem.get("id")


def text_of(elem: Optional[etree._Element]) -> Optional[str]:
    if elem is None:
        return None
    txt = (elem.text or "").strip()
    return txt if txt else None


def extract_form(form: etree._Element) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    fid = xml_id(form)
    if fid:
        out["id"] = fid
    ftype = form.get("type")
    if ftype:
        out["type"] = ftype
    orth = form.find("tei:orth", namespaces=NS)
    orth_t = text_of(orth)
    if orth_t:
        out["orth"] = orth_t
    usgs = [text_of(u) for u in form.findall("tei:usg", namespaces=NS)]
    usgs = [u for u in usgs if u]
    if usgs:
        out["usg"] = usgs

    gram = form.find("tei:gramGrp", namespaces=NS)
    if gram is not None:
        g: Dict[str, Any] = {}
        pos = text_of(gram.find("tei:pos", namespaces=NS))
        if pos:
            g["pos"] = pos
        subc = text_of(gram.find("tei:subc", namespaces=NS))
        if subc:
            g["subc"] = subc
        note = text_of(gram.find("tei:note", namespaces=NS))
        if note:
            g["note"] = note
        if g:
            out["gram"] = g

    return out


def extract_sense(sense: etree._Element) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    sid = xml_id(sense)
    if sid:
        out["id"] = sid
    # translations: look for cit[type=translation] -> quote[@xml:lang]
    translations: Dict[str, str] = {}
    for cit in sense.findall("tei:cit", namespaces=NS):
        if cit.get("type") == "translation":
            for q in cit.findall("tei:quote", namespaces=NS):
                lang = q.get("{http://www.w3.org/XML/1998/namespace}lang") or q.get("xml:lang") or q.get("lang")
                txt = text_of(q)
                if lang and txt:
                    translations[lang] = txt
    if translations:
        out["translations"] = translations
    # bibl inside cit
    bibl_texts: List[str] = []
    for b in sense.findall(".//tei:bibl", namespaces=NS):
        t = text_of(b)
        if t:
            bibl_texts.append(t)
    if bibl_texts:
        out["bibl"] = "; ".join(bibl_texts)
    return out


def extract_etym(etym: etree._Element) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    # refs inside etym (may have type, target, xml:lang)
    refs = []
    for r in etym.findall("tei:ref", namespaces=NS):
        rt = text_of(r)
        rrec: Dict[str, Any] = {}
        if rt:
            rrec["text"] = rt
        rtype = r.get("type")
        if rtype:
            rrec["type"] = rtype
        target = r.get("target")
        if target:
            rrec["target"] = target
        lang = r.get("{http://www.w3.org/XML/1998/namespace}lang") or r.get("xml:lang")
        if lang:
            rrec["lang"] = lang
        if rrec:
            refs.append(rrec)
    if refs:
        out["refs"] = refs

    # notes inside etym
    notes = [text_of(n) for n in etym.findall("tei:note", namespaces=NS)]
    notes = [n for n in notes if n]
    if notes:
        out["notes"] = notes

    # xr (cross refs) inside etym
    xrs = []
    for xr in etym.findall("tei:xr", namespaces=NS):
        xr_type = xr.get("type")
        inner = []
        for r in xr.findall("tei:ref", namespaces=NS):
            t = text_of(r)
            targ = r.get("target")
            rec: Dict[str, Any] = {}
            if t:
                rec["text"] = t
            if targ:
                rec["target"] = targ
            if rec:
                inner.append(rec)
        recxr: Dict[str, Any] = {}
        if xr_type:
            recxr["type"] = xr_type
        if inner:
            recxr["refs"] = inner
        if recxr:
            xrs.append(recxr)
    if xrs:
        out["xr"] = xrs

    return out


def parse_file(path: Path, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    tree = etree.parse(str(path))
    root = tree.getroot()
    entries = root.xpath('.//tei:entry', namespaces=NS)
    out: List[Dict[str, Any]] = []

    def elem_to_dict(elem: etree._Element) -> Any:
        """Convert an XML element into a JSON-serializable structure.

        Rules:
        - If the element has no attributes and only text (no child elements), return the text string.
        - Otherwise return a dict containing optional '@attrs', '#text', and child elements.
        - Repeated child element names are stored as lists.
        """
        # collect attributes
        data: Dict[str, Any] = {}
        attrs = {k: v for k, v in elem.items()}
        # include xml:id under its prefixed name if present
        xmlid = elem.get("{http://www.w3.org/XML/1998/namespace}id")
        if xmlid:
            attrs["xml:id"] = xmlid
        if attrs:
            data["@attrs"] = attrs

        # text (strip)
        text = (elem.text or "").strip()
        # process children
        children = list(elem)
        for child in children:
            # local name without namespace
            tag = etree.QName(child).localname
            val = elem_to_dict(child)
            if tag in data:
                # existing key: ensure it's a list
                if not isinstance(data[tag], list):
                    data[tag] = [data[tag]]
                data[tag].append(val)
            else:
                data[tag] = val

        if text and not children and not attrs:
            return text
        if text:
            data["#text"] = text
        return data

    for i, entry in enumerate(entries):
        if limit and i >= limit:
            break
        rec = elem_to_dict(entry)
        # ensure top-level xml:id is present as 'id' for convenience
        top_id = entry.get("{http://www.w3.org/XML/1998/namespace}id") or entry.get("id") or entry.get("xml:id")
        if top_id:
            # if rec is a dict, set id field; otherwise wrap
            if isinstance(rec, dict):
                rec.setdefault("id", top_id)
            else:
                rec = {"id": top_id, "value": rec}
        out.append(rec)
    return out


def main(argv: List[str]):
    if len(argv) > 1:
        p = Path(argv[1])
    else:
        p = Path(__file__).parent / "BBAW_Lexicon_of_Coptic_Egyptian-v4-2020.xml"
    if not p.exists():
        print(f"File not found: {p}")
        sys.exit(2)

    limit = None
    validate = False
    # optional --limit N and --validate
    if "--limit" in argv:
        idx = argv.index("--limit")
        try:
            limit = int(argv[idx + 1])
        except Exception:
            pass
    if "--validate" in argv:
        validate = True

    # optional validation against XSD in same folder
    if validate:
        xsd_path = Path(__file__).parent / "Coptic_Lemma_Schema-v1.2.xsd"
        if xsd_path.exists():
            try:
                schema_doc = etree.parse(str(xsd_path))
                schema = etree.XMLSchema(schema_doc)
                doc = etree.parse(str(p))
                if not schema.validate(doc):
                    print("XML validation failed. Errors:")
                    for e in schema.error_log:
                        print(e)
                else:
                    print("XML validated successfully against XSD.")
            except Exception as e:
                print("Validation failed with exception:", e)
        else:
            print(f"XSD not found at {xsd_path}; skipping validation.")

    entries = parse_file(p, limit=limit)
    out_dir = Path(__file__).parent
    jsonl_path = out_dir / "bbaw_lexicon.jsonl"
    json_path = out_dir / "bbaw_lexicon.json"

    with jsonl_path.open("w", encoding="utf-8") as jl:
        for r in entries:
            jl.write(json.dumps(r, ensure_ascii=False) + "\n")

    with json_path.open("w", encoding="utf-8") as j:
        json.dump(entries, j, ensure_ascii=False, indent=2)

    print(f"Wrote {len(entries)} entries to:\n - {jsonl_path}\n - {json_path}")


if __name__ == "__main__":
    main(sys.argv)

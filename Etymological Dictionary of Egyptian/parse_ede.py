"""
Parser for the Etymological Dictionary of Egyptian (EDE) PDF

This parser extracts the full text for each lemma entry from the PDF,
preserving structure and preparing data for further etymological and definitional analysis.

The EDE typically structures entries with:
- Lemma headword (often in bold or distinct formatting)
- Transliteration
- Hieroglyphic writing
- Part of speech
- Definitions and meanings
- Etymological information
- Cross-references
- Citations and attestations
"""

import fitz  # PyMuPDF
import json
import re
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict


class EDEParser:
    """Parser for Etymological Dictionary of Egyptian"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.doc = None
        self.lemmas = []
        
    def open_pdf(self):
        """Open the PDF document"""
        print(f"Opening PDF: {self.pdf_path}")
        self.doc = fitz.open(self.pdf_path)
        print(f"PDF opened: {len(self.doc)} pages")
        
    def close_pdf(self):
        """Close the PDF document"""
        if self.doc:
            self.doc.close()
            
    def extract_page_text(self, page_num: int) -> str:
        """Extract raw text from a page"""
        page = self.doc[page_num]
        return page.get_text()
    
    def extract_page_blocks(self, page_num: int) -> List[Dict[str, Any]]:
        """
        Extract text blocks from a page with positioning and formatting info.
        Returns list of block dictionaries with text, bbox, font info, etc.
        """
        page = self.doc[page_num]
        blocks = []
        
        # Get text as dictionary which includes detailed formatting
        text_dict = page.get_text("dict")
        
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # Text block
                block_info = {
                    "bbox": block.get("bbox"),
                    "lines": []
                }
                
                for line in block.get("lines", []):
                    line_info = {
                        "bbox": line.get("bbox"),
                        "spans": []
                    }
                    
                    for span in line.get("spans", []):
                        span_info = {
                            "text": span.get("text", ""),
                            "font": span.get("font", ""),
                            "size": span.get("size", 0),
                            "flags": span.get("flags", 0),  # Bold, italic, etc.
                            "color": span.get("color", 0)
                        }
                        line_info["spans"].append(span_info)
                    
                    block_info["lines"].append(line_info)
                blocks.append(block_info)
                
        return blocks
    
    def _extract_pos_and_definition(self, line_text: str, headword: str) -> tuple:
        """
        Extract part of speech and definition from headword line.
        Format: headword (part of speech) "definition text"
        or: headword "definition text"
        """
        pos = None
        definition = None
        
        # Remove headword from line
        remaining = line_text.replace(headword, "", 1).strip()
        
        # Look for POS in parentheses right after headword
        pos_match = re.match(r'^\(([^)]+)\)', remaining)
        if pos_match:
            pos = pos_match.group(1).strip()
            remaining = remaining[pos_match.end():].strip()
        
        # Look for definition in quotes
        def_match = re.search(r'"([^"]+)"', remaining)
        if def_match:
            definition = def_match.group(1).strip()
        elif remaining and len(remaining) < 200:
            # If no quotes but short text, might be definition
            definition = remaining.strip()
        
        return pos, definition
    
    def _is_etymology_section(self, text: str) -> bool:
        """
        Detect if a paragraph is an etymology section.
        Etymology sections typically start with bullets (•), nb:, lit:, or numbered points,
        or contain comparative linguistic data with language family references.
        """
        text_lower = text.lower().strip()
        
        # Check for common etymology markers
        etymology_markers = [
            text_lower.startswith('nb:'),
            text_lower.startswith('nb1:'),
            text_lower.startswith('nb2:'),
            text_lower.startswith('nb3:'),
            text_lower.startswith('lit:'),
            text_lower.startswith('•'),
            text_lower.startswith('1.') and 'etymology' in text_lower,
            text_lower.startswith('2.') and len(text_lower) < 500,
            'descended from' in text_lower,
            'cognate' in text_lower or text_lower.startswith('cognate'),
            'borrowed from' in text_lower,
            'related to' in text_lower,
            # Afro-Asiatic heritage markers
            text_lower.startswith('common aa'),
            'common aa heritage' in text_lower,
            'common aa,' in text_lower,
            # Language family comparison patterns (cp. = compare)
            text_lower.startswith('cp. sem.') or text_lower.startswith('cp. cu.') or text_lower.startswith('cp. ch.'),
            text_lower.startswith('pre x of'),  # Morphological etymology
            text_lower.startswith('prefix of'),
        ]
        
        # Also check for multiple language family references (strong indicator of etymology)
        # Sem. (Semitic), Cu. (Cushitic), Ch. (Chadic), Brb. (Berber), etc.
        lang_families = ['sem.', 'cu.', 'ch.', 'brb.', 'lecu.', 'hecu.', 'wch.', 'cch.', 'ech.']
        family_count = sum(1 for fam in lang_families if fam in text_lower)
        if family_count >= 2:
            etymology_markers.append(True)
        
        return any(etymology_markers)
    
    def _finalize_lemma_structure(self, lemma: Dict[str, Any]):
        """
        Post-process lemma to clean up and organize data.
        """
        # Remove duplicate text field (we have paragraphs now)
        # but keep it for backward compatibility
        pass
    
    def is_lemma_headword(self, span_info: Dict[str, Any], line_position: int = 0) -> bool:
        """
        Detect if a text span is likely a lemma headword.
        In the EDE, headwords are:
        - Bold (BaskervilleMT-Bold or BaskervilleSmallCapMT)
        - At or near the start of a line
        - Often contain Egyptian transliteration characters or reconstructed forms (*)
        """
        flags = span_info.get("flags", 0)
        size = span_info.get("size", 0)
        text = span_info.get("text", "").strip()
        font = span_info.get("font", "")
        
        # Exclude common non-lemma text
        excluded_patterns = ['lit', 'nb', 'NB', 'Cp.', 'cp.', 'cf.', 'Cf.', 'v.', 'vs.']
        if any(text.startswith(p) for p in excluded_patterns):
            return False
        
        # Exclude numeric patterns like "1.", "2.", etc.
        if re.match(r'^\d+\.?$', text):
            return False
        
        # Check for bold (flag bit 4 = 16 in PyMuPDF)
        is_bold = bool(flags & 16)
        
        # Check if text looks like a lemma (contains Egyptian chars or reconstructed forms)
        egyp_chars = any(c in text for c in ['ꜣ', 'ꜥ', 'ḫ', 'ḥ', 'ẖ', 'ḏ', 'ṯ', 'š', 'ś', 'ḳ', 'ṣ', 'ṭ', '*', 'ʿ', '-', 'ˁ'])
        
        # TYPE 1: Bold headwords with * or Egyptian chars (like "*m . . .")
        if is_bold and "Bold" in font and line_position <= 1:
            if text.startswith('*') or egyp_chars:
                return True
        
        # TYPE 2: SmallCap headwords at size 11.0 (main lemma entries like "m", "m-")
        # These are short (1-5 chars) and appear at line start
        if "SmallCap" in font and size >= 10.5 and line_position <= 1:
            # Short text that's alphanumeric or contains Egyptian chars
            if 1 <= len(text) <= 5 and (text.isalpha() or egyp_chars or '-' in text):
                return True
        
        # TYPE 3: Single/short bold headwords at size >= 10.5 at VERY start of line (position 0)
        # This catches lemmas like "m (non-encl. part.)" that are regular Bold, not SmallCap
        # Must be at position 0 to avoid false positives from bold text mid-line
        if is_bold and size >= 10.5 and line_position == 0:
            # Very short text (1-4 chars) that's alphanumeric
            if 1 <= len(text) <= 4 and (text.isalnum() or egyp_chars or '-' in text or '.' in text):
                # Extra safety: must start with a letter (not just numbers)
                if text[0].isalpha() or text[0] in ['*', '(']:
                    return True
        
        return False
    
    def extract_lemma_from_blocks(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract lemma entries from text blocks.
        Each lemma typically starts with a headword and continues until the next headword.
        In the EDE, lemmas are separated by bold headwords at the start of paragraphs.
        
        Enhanced to:
        - Filter out small text (< 10pt)
        - Preserve paragraph structure
        - Extract POS from headword line
        - Separate definitions from etymology sections
        """
        lemmas = []
        current_lemma = None
        current_paragraph = []
        
        for block in blocks:
            block_text = ""
            block_lines = []
            
            for line in block.get("lines", []):
                line_text = ""
                line_spans = []
                
                # Collect all spans in the line, filtering small text
                for span_idx, span in enumerate(line.get("spans", [])):
                    text = span.get("text", "").strip()
                    size = span.get("size", 0)
                    
                    # Filter out small text (footnotes, subscripts, etc.)
                    if size < 10.0:
                        continue
                        
                    if text:
                        line_spans.append((span_idx, span, text))
                        line_text += text + " "
                
                if not line_spans:
                    continue
                
                block_lines.append((line, line_text, line_spans))
            
            # Process all lines in this block
            for line, line_text, line_spans in block_lines:
                # Check if the first span (or early span) is a headword
                headword_found = False
                # First, check first few spans for explicit headwords
                for span_idx, span, text in line_spans[:6]:  # Check first 6 spans to catch short headwords
                    if self.is_lemma_headword(span, span_idx):
                        # Save previous lemma if exists and has substantial content
                        if current_lemma and len(current_lemma["text"].strip()) > 20:
                            # Finalize the previous lemma
                            self._finalize_lemma_structure(current_lemma)
                            lemmas.append(current_lemma)

                        # Extract POS and definition from headword line
                        pos, definition = self._extract_pos_and_definition(line_text, text)
                        
                        # Start new lemma
                        current_lemma = {
                            "headword": text,
                            "part_of_speech": pos,
                            "definition": definition,
                            "text": line_text.strip() + "\n",
                            "paragraphs": [line_text.strip()],
                            "etymology_sections": [],
                            "font_info": {
                                "font": span.get("font", ""),
                                "size": span.get("size", 0),
                                "flags": span.get("flags", 0)
                            }
                        }
                        current_paragraph = []
                        headword_found = True
                        break

                # If still not found, detect short headword span followed immediately by a definition-like span
                if not headword_found:
                    for i in range(min(5, len(line_spans)-1)):
                        span_idx, span, text = line_spans[i]
                        nxt_idx, nxt_span, nxt_text = line_spans[i+1]
                        # candidate: very short span (1-4 chars) with Bold/SmallCap font
                        if 1 <= len(text) <= 4 and ("Bold" in span.get('font','') or "SmallCap" in span.get('font','')):
                            # Skip obviously non-lemma markers (numbers, list markers, nb, lit etc.)
                            low = text.lower()
                            if low.startswith(('nb', 'lit', 'cp', 'cf')):
                                continue
                            if re.match(r'^[\d\(\)\.\-]+$', text):
                                continue
                            # ensure the candidate contains a letter or Egyptian char (avoid pure digits)
                            if not re.search(r"[A-Za-zꜣꜥḫḥẖḏṯšśḳṣṭʿ]", text) and '*' not in text and '-' not in text:
                                continue
                            # next span looks like a definition if it begins with a quote or contains a comma and short phrase
                            if nxt_text.startswith('"') or nxt_text.startswith('“') or (',' in nxt_text and len(nxt_text.split()) < 10):
                                if current_lemma and len(current_lemma["text"].strip()) > 20:
                                    self._finalize_lemma_structure(current_lemma)
                                    lemmas.append(current_lemma)
                                
                                # Extract POS and definition from headword line
                                pos, definition = self._extract_pos_and_definition(line_text, text)
                                
                                current_lemma = {
                                    "headword": text,
                                    "part_of_speech": pos,
                                    "definition": definition,
                                    "text": line_text.strip() + "\n",
                                    "paragraphs": [line_text.strip()],
                                    "etymology_sections": [],
                                    "font_info": {
                                        "font": span.get("font", ""),
                                        "size": span.get("size", 0),
                                        "flags": span.get("flags", 0)
                                    }
                                }
                                current_paragraph = []
                                headword_found = True
                                break
                
                # If no headword found but we have a current lemma, append to it
                if not headword_found and current_lemma:
                    current_lemma["text"] += line_text.strip() + "\n"
                    
                    # Accumulate text for current paragraph
                    if line_text.strip():
                        current_paragraph.append(line_text.strip())
            
            # Block boundary = paragraph boundary in PDF
            if current_lemma and current_paragraph:
                para_text = " ".join(current_paragraph)
                current_lemma["paragraphs"].append(para_text)
                
                # Check if this paragraph is an etymology section
                if self._is_etymology_section(para_text):
                    current_lemma["etymology_sections"].append(para_text)
                
                current_paragraph = []
        
        # Don't forget the last lemma
        if current_lemma and len(current_lemma["text"].strip()) > 20:
            # Add any remaining paragraph
            if current_paragraph:
                para_text = " ".join(current_paragraph)
                current_lemma["paragraphs"].append(para_text)
                if self._is_etymology_section(para_text):
                    current_lemma["etymology_sections"].append(para_text)
            
            self._finalize_lemma_structure(current_lemma)
            lemmas.append(current_lemma)
            
        return lemmas
    
    def parse_page(self, page_num: int) -> List[Dict[str, Any]]:
        """Parse a single page and extract lemmas"""
        print(f"Parsing page {page_num + 1}...")
        blocks = self.extract_page_blocks(page_num)
        lemmas = self.extract_lemma_from_blocks(blocks)
        
        # Add page number to each lemma
        for lemma in lemmas:
            lemma["page"] = page_num + 1
            
        return lemmas
    
    def parse_pages(self, start_page: int = 0, end_page: int = None) -> List[Dict[str, Any]]:
        """
        Parse a range of pages.
        If end_page is None, parse until the end of the document.
        """
        if not self.doc:
            self.open_pdf()
            
        if end_page is None:
            end_page = len(self.doc)
        
        all_lemmas = []
        
        for page_num in range(start_page, min(end_page, len(self.doc))):
            page_lemmas = self.parse_page(page_num)
            all_lemmas.extend(page_lemmas)
            
        self.lemmas = all_lemmas
        return all_lemmas
    
    def clean_lemma_text(self, text: str) -> str:
        """Clean up extracted lemma text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove hyphenation at line breaks
        text = re.sub(r'-\s+', '', text)
        return text.strip()
    
    def export_to_json(self, output_path: str, pretty: bool = True):
        """Export parsed lemmas to JSON file"""
        print(f"Exporting {len(self.lemmas)} lemmas to {output_path}...")
        
        # Clean lemma texts
        for lemma in self.lemmas:
            lemma["text"] = self.clean_lemma_text(lemma["text"])
        
        with open(output_path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(self.lemmas, f, ensure_ascii=False, indent=2)
            else:
                json.dump(self.lemmas, f, ensure_ascii=False)
                
        print(f"Export complete!")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about parsed lemmas"""
        stats = {
            "total_lemmas": len(self.lemmas),
            "pages_covered": len(set(l["page"] for l in self.lemmas)),
            "avg_text_length": sum(len(l["text"]) for l in self.lemmas) / len(self.lemmas) if self.lemmas else 0,
            "sample_headwords": [l["headword"] for l in self.lemmas[:10]]
        }
        return stats


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Parse the Etymological Dictionary of Egyptian PDF"
    )
    parser.add_argument(
        "--pdf",
        type=str,
        default="Etymological-Dictionary-of-Egyptian-vol3.pdf",
        help="Path to the PDF file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="ede_lemmas.json",
        help="Output JSON file"
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=33,  # Page 34 in PDF (0-indexed)
        help="Starting page number (0-indexed, default=33 for page 34 where lemmas begin)"
    )
    parser.add_argument(
        "--end-page",
        type=int,
        default=None,
        help="Ending page number (exclusive). If not specified, parse all pages."
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: only parse first 5 pages"
    )
    
    args = parser.parse_args()
    
    # Initialize parser
    ede = EDEParser(args.pdf)
    ede.open_pdf()
    
    # Determine page range
    if args.test:
        print("Running in test mode: parsing first 5 pages only")
        end_page = min(5, len(ede.doc))
    else:
        end_page = args.end_page
    
    # Parse pages
    lemmas = ede.parse_pages(start_page=args.start_page, end_page=end_page)
    
    # Show statistics
    stats = ede.get_statistics()
    print("\n" + "="*60)
    print("PARSING STATISTICS")
    print("="*60)
    print(f"Total lemmas extracted: {stats['total_lemmas']}")
    print(f"Pages covered: {stats['pages_covered']}")
    print(f"Average text length: {stats['avg_text_length']:.1f} characters")
    print(f"\nFirst 10 headwords:")
    for hw in stats['sample_headwords']:
        print(f"  - {hw}")
    print("="*60)
    
    # Export to JSON
    ede.export_to_json(args.output)
    
    # Close PDF
    ede.close_pdf()
    
    print(f"\nDone! Lemmas saved to: {args.output}")


if __name__ == "__main__":
    main()

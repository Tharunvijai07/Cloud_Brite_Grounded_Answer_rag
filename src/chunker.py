import re
import os
import glob
from typing import List, Dict, Any, Optional
from src.loader import load_policy_manual


def extract_cross_references(text: str) -> List[str]:
    """Finds all §x.y.z and section references in the text."""
    refs = re.findall(r'§(\d+(?:\.\d+)+[A-Za-z]?)', text)
    return sorted(list(set(refs)))


def _extract_effective_date_from_header(text: str, fallback: str = "2025-12-31") -> str:
    """
    Attempts to read the effective date from a Markdown document header.
    Accepts formats like:
      - Effective: 2025-12-31
      - Effective Date: 1 January 2026
      - Effective 1 March 2026
    Returns an ISO date string 'YYYY-MM-DD', or *fallback* if none is found.
    """
    MONTH_MAP = {
        'january': '01', 'jan': '01', 'february': '02', 'feb': '02',
        'march': '03', 'mar': '03', 'april': '04', 'apr': '04',
        'may': '05', 'june': '06', 'jun': '06', 'july': '07', 'jul': '07',
        'august': '08', 'aug': '08', 'september': '09', 'sep': '09',
        'october': '10', 'oct': '10', 'november': '11', 'nov': '11',
        'december': '12', 'dec': '12',
    }

    # Only scan the first 30 lines (header region)
    header = "\n".join(text.split("\n")[:30]).lower()

    # Pattern: YYYY-MM-DD
    iso = re.search(r'effective[^:]*:\s*(\d{4}-\d{2}-\d{2})', header)
    if iso:
        return iso.group(1)

    # Pattern: D Month YYYY  or  Month D YYYY  or  Month YYYY
    wordy = re.search(
        r'effective[^:]*[:\s]+(\d{1,2})?\s*([a-z]+)\s+(\d{4})',
        header
    )
    if wordy:
        day_str, month_str, year = wordy.group(1), wordy.group(2), wordy.group(3)
        month = MONTH_MAP.get(month_str)
        if month:
            day = day_str.zfill(2) if day_str else "01"
            return f"{year}-{month}-{day}"

    return fallback


def _extract_amendment_id_from_filename(source_doc: str) -> str:
    """
    Derives a slug like 'amendment_2026_01' from a filename such as
    'Amendment No. 2026-01.md' or 'amendment-2026-02.md'.
    Falls back to the raw filename stem.
    """
    stem = os.path.splitext(source_doc)[0]
    # Normalise separators and extract numbers
    digits = re.findall(r'\d+', stem)
    if digits:
        return "amendment_" + "_".join(digits)
    return re.sub(r'[^a-z0-9]', '_', stem.lower()).strip('_')


def parse_policy_manual_chunks(text: str, source_doc: str = "policy-manual.md") -> List[Dict[str, Any]]:
    """
    Parses the consolidated base policy manual into clause-level chunks
    using Markdown headers and bold clause markers (**x.y.z**).
    The effective date is read from the document header; falls back to '2025-12-31'.
    """
    # --- 1.1: read effective date from the document itself ---
    effective_date = _extract_effective_date_from_header(text, fallback="2025-12-31")

    chunks = []
    lines = text.split("\n")

    current_part = "Preamble"
    current_section = "General"
    current_clause_id = None
    current_clause_heading = "General"
    current_clause_lines = []

    part_pattern = re.compile(r"^#\s+(Part\s+\d+.*?)$", re.IGNORECASE)
    section_pattern = re.compile(r"^##\s+(\d+\.\d+\s+.*?)$")
    clause_start_pattern = re.compile(r"^\*\*(\d+\.\d+\.\d+[A-Za-z]?)\*\*(?:\s+(.*?))?(?:\s*—\s*(.*))?$")

    def flush_clause():
        nonlocal current_clause_id, current_clause_heading, current_clause_lines
        if current_clause_id and current_clause_lines:
            raw_body = "\n".join(current_clause_lines).strip()
            if raw_body:
                chunks.append({
                    "clause_id": current_clause_id,
                    "display_id": f"§{current_clause_id}",
                    "heading": current_clause_heading,
                    "part": current_part,
                    "section": current_section,
                    "text": raw_body,
                    "effective_date": effective_date,   # ← dynamic, not hardcoded
                    "source_doc": source_doc,
                    "cross_references": extract_cross_references(raw_body)
                })
        current_clause_id = None
        current_clause_lines = []

    for line in lines:
        part_match = part_pattern.match(line)
        if part_match:
            flush_clause()
            current_part = part_match.group(1).strip()
            continue

        section_match = section_pattern.match(line)
        if section_match:
            flush_clause()
            current_section = section_match.group(1).strip()
            continue

        clause_match = clause_start_pattern.match(line.strip())
        if clause_match:
            flush_clause()
            current_clause_id = clause_match.group(1)
            inline_title = clause_match.group(2) or clause_match.group(3) or current_section
            current_clause_heading = inline_title.strip() if inline_title else current_section
            current_clause_lines = [line.strip()]
        else:
            if current_clause_id:
                current_clause_lines.append(line)

    flush_clause()
    return chunks


def parse_amendment_chunks(text: str, source_doc: str = "Amendment No. 2026-01.md") -> List[Dict[str, Any]]:
    """
    Generic amendment parser.
    - Reads the effective date from the document header (e.g. 'Effective 1 March 2026').
    - Derives an amendment slug from the filename so any Amendment No. YYYY-NN.md is handled.
    """
    # --- 1.1: read effective date & amendment id generically ---
    effective_date = _extract_effective_date_from_header(text, fallback="2026-03-01")
    amendment_slug = _extract_amendment_id_from_filename(source_doc)
    amendment_display = os.path.splitext(source_doc)[0]  # e.g. "Amendment No. 2026-01"

    chunks = []
    lines = text.split("\n")

    current_section = "Amendment Overview"
    current_para_id = None
    current_para_lines = []

    sec_pattern = re.compile(r"^##\s+(\d+\.\s+.*?)$")
    para_pattern = re.compile(r"^\*\*(\d+\.\d+)\*\*\s+(.*)$")

    def flush_para():
        nonlocal current_para_id, current_para_lines, current_section
        if current_para_id and current_para_lines:
            raw_body = "\n".join(current_para_lines).strip()
            if raw_body:
                chunks.append({
                    "clause_id": f"{amendment_slug}_{current_para_id}",
                    "display_id": f"{amendment_display} §{current_para_id}",
                    "heading": f"{amendment_display}: {current_section}",
                    "part": f"{amendment_display} (Effective {effective_date})",
                    "section": current_section,
                    "text": raw_body,
                    "effective_date": effective_date,   # ← dynamic
                    "source_doc": source_doc,
                    "cross_references": extract_cross_references(raw_body)
                })
        current_para_id = None
        current_para_lines = []

    for line in lines:
        sec_match = sec_pattern.match(line)
        if sec_match:
            flush_para()
            current_section = sec_match.group(1).strip()
            continue

        para_match = para_pattern.match(line.strip())
        if para_match:
            flush_para()
            current_para_id = para_match.group(1)
            current_para_lines = [line.strip()]
        else:
            if current_para_id:
                current_para_lines.append(line)

    flush_para()
    return chunks


def load_and_parse_all_corpus(corpus_dir: str = "corpus") -> List[Dict[str, Any]]:
    """
    Dynamically loads and chunks ALL .md files in *corpus_dir*.
    - Files whose name matches 'amendment' (case-insensitive) are parsed with
      parse_amendment_chunks().
    - All other .md files are parsed with parse_policy_manual_chunks().
    No code change is needed when new corpus documents or amendments are added.
    """
    all_chunks: List[Dict[str, Any]] = []

    md_files = sorted(glob.glob(os.path.join(corpus_dir, "*.md")))
    if not md_files:
        return all_chunks

    for file_path in md_files:
        filename = os.path.basename(file_path)
        try:
            content = load_policy_manual(file_path)
        except FileNotFoundError:
            continue

        if re.search(r'amendment', filename, re.IGNORECASE):
            all_chunks.extend(parse_amendment_chunks(content, source_doc=filename))
        else:
            all_chunks.extend(parse_policy_manual_chunks(content, source_doc=filename))

    return all_chunks

import re
import os
from typing import List, Dict, Any
from src.loader import load_policy_manual


def extract_cross_references(text: str) -> List[str]:
    """Finds all §x.y.z and section references in the text."""
    refs = re.findall(r'§(\d+(?:\.\d+)+[A-Za-z]?)', text)
    return sorted(list(set(refs)))


def parse_policy_manual_chunks(text: str, source_doc: str = "policy-manual.md") -> List[Dict[str, Any]]:
    """
    Parses the consolidated base policy manual into clause-level chunks
    using Markdown headers and bold clause markers (**x.y.z**).
    """
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
                    "effective_date": "2025-12-31",
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
    Parses Amendment No. 2026-01 into structured chunks with effective date 2026-03-01.
    """
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
                    "clause_id": f"amendment_2026_01_{current_para_id}",
                    "display_id": f"Amendment No. 2026-01 §{current_para_id}",
                    "heading": f"Amendment No. 2026-01: {current_section}",
                    "part": "Amendment No. 2026-01 (Effective 1 March 2026)",
                    "section": current_section,
                    "text": raw_body,
                    "effective_date": "2026-03-01",
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
    """Loads and chunks all policy documents in the corpus directory."""
    all_chunks = []
    
    manual_path = os.path.join(corpus_dir, "policy-manual.md")
    if os.path.exists(manual_path):
        all_chunks.extend(parse_policy_manual_chunks(load_policy_manual(manual_path)))
        
    amendment_path = os.path.join(corpus_dir, "Amendment No. 2026-01.md")
    if os.path.exists(amendment_path):
        all_chunks.extend(parse_amendment_chunks(load_policy_manual(amendment_path)))

    return all_chunks

import re
import os
import sys
from typing import List, Dict, Any

# Ensure workspace root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.loader import load_policy_manual


def parse_chunks(raw_text: str, default_effective_date: str = "2025-12-31") -> List[Dict[str, Any]]:
    """
    Parses the raw Markdown text of a policy manual or amendment into structured chunks.
    
    Each chunk corresponds to a clause keyed by its §x.y.z ID and includes:
    - clause_id: Clause identifier string (e.g., '4.3.2' or 'A2026-01-1.1')
    - text: Full raw text of the clause including sub-bullets and tables
    - part: The section part heading (e.g., 'Part 4' or 'Amendment 2026-01')
    - heading: The section sub-heading (e.g., 'Recipient obligations')
    - effective_date: ISO date string (e.g., '2025-12-31' or '2026-03-01')

    Args:
        raw_text: The complete Markdown text of the manual or amendment.
        default_effective_date: Default effective date for clauses in this text.

    Returns:
        A list of chunk dictionaries.
    """
    lines = raw_text.splitlines(keepends=True)
    chunks = []
    
    current_part = ""
    current_heading = ""
    current_clause_id = None
    current_text_lines = []

    # Regex patterns
    part_pattern = re.compile(r'^#\s+(Part\s+\d+|Amendment\s+.*)', re.IGNORECASE)
    heading_pattern = re.compile(r'^##\s+(\d+\.\d+|\d+)\s+(.*)')
    clause_pattern = re.compile(r'^\*\*(\d+\.\d+\.\d+|\d+\.\d+)(?:[^*]*)\*\*\s*')

    def finalize_chunk():
        nonlocal current_clause_id, current_text_lines
        if current_clause_id:
            full_text = "".join(current_text_lines).strip()
            chunks.append({
                "clause_id": current_clause_id,
                "text": full_text,
                "part": current_part,
                "heading": current_heading,
                "effective_date": default_effective_date
            })
            current_clause_id = None
            current_text_lines = []

    for line in lines:
        part_match = part_pattern.match(line)
        if part_match:
            finalize_chunk()
            current_part = part_match.group(1).strip()
            continue

        heading_match = heading_pattern.match(line)
        if heading_match:
            finalize_chunk()
            current_heading = heading_match.group(2).strip()
            continue

        clause_match = clause_pattern.match(line)
        if clause_match:
            finalize_chunk()
            current_clause_id = clause_match.group(1)
            current_text_lines.append(line)
            continue

        if current_clause_id:
            if line.strip() == "---" or line.startswith("#"):
                finalize_chunk()
            else:
                current_text_lines.append(line)

    finalize_chunk()
    return chunks


def load_and_parse_all_corpus(corpus_dir: str = "corpus") -> List[Dict[str, Any]]:
    """
    Loads all corpus files (base manual + amendments) and parses them into structured chunks
    tagged with their respective effective dates.
    """
    all_chunks = []
    
    base_manual_path = os.path.join(corpus_dir, "policy-manual.md")
    if os.path.exists(base_manual_path):
        base_text = load_policy_manual(base_manual_path)
        base_chunks = parse_chunks(base_text, default_effective_date="2025-12-31")
        all_chunks.extend(base_chunks)

    amendment_path = os.path.join(corpus_dir, "Amendment No. 2026-01.md")
    if os.path.exists(amendment_path):
        amendment_text = load_policy_manual(amendment_path)
        amendment_chunks = parse_chunks(amendment_text, default_effective_date="2026-03-01")
        all_chunks.extend(amendment_chunks)

    return all_chunks


if __name__ == "__main__":
    chunks = load_and_parse_all_corpus()
    print(f"Total Corpus Chunks Extracted: {len(chunks)}")
    print(f"Base Manual Chunks (2025-12-31): {len([c for c in chunks if c['effective_date'] == '2025-12-31'])}")
    print(f"Amendment 2026-01 Chunks (2026-03-01): {len([c for c in chunks if c['effective_date'] == '2026-03-01'])}")

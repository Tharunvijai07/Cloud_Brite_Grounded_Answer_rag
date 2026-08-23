import re
import os
import sys
from typing import List, Dict, Any

# Ensure workspace root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.loader import load_policy_manual


def parse_chunks(raw_text: str) -> List[Dict[str, Any]]:
    """
    Parses the raw Markdown text of the policy manual into structured chunks.
    
    Each chunk corresponds to a clause keyed by its §x.y.z ID and includes:
    - clause_id: Clause identifier string (e.g., '4.3.2')
    - text: Full raw text of the clause including sub-bullets and tables
    - part: The section part heading (e.g., 'Part 4')
    - heading: The section sub-heading (e.g., 'Recipient obligations')

    Args:
        raw_text: The complete Markdown text of the manual.

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
    part_pattern = re.compile(r'^#\s+(Part\s+\d+)', re.IGNORECASE)
    heading_pattern = re.compile(r'^##\s+\d+\.\d+\s+(.*)')
    # Clause pattern matching **x.y.z** or **x.y.z Title** at line start
    clause_pattern = re.compile(r'^\*\*(\d+\.\d+\.\d+)(?:[^*]*)\*\*\s*')

    def finalize_chunk():
        nonlocal current_clause_id, current_text_lines
        if current_clause_id:
            full_text = "".join(current_text_lines).strip()
            chunks.append({
                "clause_id": current_clause_id,
                "text": full_text,
                "part": current_part,
                "heading": current_heading
            })
            current_clause_id = None
            current_text_lines = []

    for line in lines:
        # Check for Part header
        part_match = part_pattern.match(line)
        if part_match:
            finalize_chunk()
            current_part = part_match.group(1).strip()
            continue

        # Check for Section Heading
        heading_match = heading_pattern.match(line)
        if heading_match:
            finalize_chunk()
            current_heading = heading_match.group(1).strip()
            continue

        # Check for Clause start
        clause_match = clause_pattern.match(line)
        if clause_match:
            finalize_chunk()
            current_clause_id = clause_match.group(1)
            current_text_lines.append(line)
            continue

        # Accumulate text lines if inside a clause
        if current_clause_id:
            # Horizontal rules or new top-level markdown headers end the clause
            if line.strip() == "---" or line.startswith("#"):
                finalize_chunk()
            else:
                current_text_lines.append(line)

    finalize_chunk()
    return chunks


if __name__ == "__main__":
    raw_manual = load_policy_manual()
    all_chunks = parse_chunks(raw_manual)
    print(f"Total Chunks Extracted: {len(all_chunks)}")
    unique_ids = set(c["clause_id"] for c in all_chunks)
    print(f"Unique Clause IDs: {len(unique_ids)}")
    print("-" * 80)
    for i, c in enumerate(all_chunks, 1):
        clean_text = c['text'].replace('\n', ' ')
        preview = clean_text[:60] + "..." if len(clean_text) > 60 else clean_text
        print(f"{i:3d}. [{c['part']}] [{c['heading']}] §{c['clause_id']}: {preview}")


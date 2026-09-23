"""
tests/test_chunker.py
Unit tests for src/chunker.py — parser regex and effective-date extraction.
Run with:  python -m pytest tests/test_chunker.py -v
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.chunker import (
    parse_policy_manual_chunks,
    parse_amendment_chunks,
    _extract_effective_date_from_header,
    _extract_amendment_id_from_filename,
    extract_cross_references,
)


# ---------------------------------------------------------------------------
# Effective-date extraction
# ---------------------------------------------------------------------------

class TestExtractEffectiveDateFromHeader:
    def test_iso_format(self):
        text = "# Policy Manual\nEffective Date: 2025-12-31\n\nContent here."
        assert _extract_effective_date_from_header(text) == "2025-12-31"

    def test_wordy_format_day_month_year(self):
        text = "# Amendment\nEffective 1 March 2026\n\nContent here."
        assert _extract_effective_date_from_header(text) == "2026-03-01"

    def test_wordy_format_month_year_only(self):
        text = "# Doc\nEffective: January 2027\n\n"
        assert _extract_effective_date_from_header(text) == "2027-01-01"

    def test_fallback_when_no_date(self):
        text = "# Policy Manual\n\nNo date here.\n"
        assert _extract_effective_date_from_header(text, fallback="2025-12-31") == "2025-12-31"


# ---------------------------------------------------------------------------
# Amendment ID from filename
# ---------------------------------------------------------------------------

class TestExtractAmendmentIdFromFilename:
    def test_standard_format(self):
        assert _extract_amendment_id_from_filename("Amendment No. 2026-01.md") == "amendment_2026_01"

    def test_hyphen_format(self):
        assert _extract_amendment_id_from_filename("amendment-2026-02.md") == "amendment_2026_02"


# ---------------------------------------------------------------------------
# Cross-reference extraction
# ---------------------------------------------------------------------------

class TestExtractCrossReferences:
    def test_single_ref(self):
        assert extract_cross_references("See §4.3.2 for details.") == ["4.3.2"]

    def test_multiple_refs(self):
        refs = extract_cross_references("See §4.3.2 and §9.1.4 and again §4.3.2.")
        assert refs == ["4.3.2", "9.1.4"]  # deduplicated and sorted

    def test_no_refs(self):
        assert extract_cross_references("No references here.") == []


# ---------------------------------------------------------------------------
# Policy manual parser
# ---------------------------------------------------------------------------

SAMPLE_POLICY = """\
# Part 1 General Provisions

## 1.1 Definitions

**1.1.1** Definition of Household — A group of individuals sharing a residence.

**1.1.2** Definition of Income — All monetary receipts before deductions.

## 1.2 Eligibility

**1.2.1** Residency Requirement — Applicant must reside in Calder County.
"""

class TestParsePolicyManualChunks:
    def test_returns_chunks(self):
        chunks = parse_policy_manual_chunks(SAMPLE_POLICY)
        assert len(chunks) == 3

    def test_clause_ids(self):
        chunks = parse_policy_manual_chunks(SAMPLE_POLICY)
        ids = [c["clause_id"] for c in chunks]
        assert "1.1.1" in ids
        assert "1.1.2" in ids
        assert "1.2.1" in ids

    def test_part_assigned(self):
        chunks = parse_policy_manual_chunks(SAMPLE_POLICY)
        assert all(c["part"] == "Part 1 General Provisions" for c in chunks)

    def test_section_assigned(self):
        chunks = parse_policy_manual_chunks(SAMPLE_POLICY)
        c = next(c for c in chunks if c["clause_id"] == "1.2.1")
        assert "1.2" in c["section"]

    def test_effective_date_fallback(self):
        chunks = parse_policy_manual_chunks(SAMPLE_POLICY)
        # No date in SAMPLE_POLICY header → fallback
        assert all(c["effective_date"] == "2025-12-31" for c in chunks)

    def test_effective_date_from_header(self):
        text = "Effective Date: 2024-07-01\n" + SAMPLE_POLICY
        chunks = parse_policy_manual_chunks(text)
        assert all(c["effective_date"] == "2024-07-01" for c in chunks)

    def test_display_id_format(self):
        chunks = parse_policy_manual_chunks(SAMPLE_POLICY)
        assert all(c["display_id"].startswith("§") for c in chunks)


# ---------------------------------------------------------------------------
# Amendment parser
# ---------------------------------------------------------------------------

SAMPLE_AMENDMENT = """\
# Amendment No. 2026-01
Effective 1 March 2026

## 1. Reporting Timelines

**1.1** All changes of circumstances must be reported within 14 calendar days.

**1.2** Failure to report constitutes a policy violation under §9.1.4.
"""

class TestParseAmendmentChunks:
    def test_returns_chunks(self):
        chunks = parse_amendment_chunks(SAMPLE_AMENDMENT, source_doc="Amendment No. 2026-01.md")
        assert len(chunks) == 2

    def test_effective_date_from_header(self):
        chunks = parse_amendment_chunks(SAMPLE_AMENDMENT, source_doc="Amendment No. 2026-01.md")
        assert all(c["effective_date"] == "2026-03-01" for c in chunks)

    def test_generic_slug(self):
        chunks = parse_amendment_chunks(SAMPLE_AMENDMENT, source_doc="Amendment No. 2026-01.md")
        assert all(c["clause_id"].startswith("amendment_2026_01_") for c in chunks)

    def test_cross_references(self):
        chunks = parse_amendment_chunks(SAMPLE_AMENDMENT, source_doc="Amendment No. 2026-01.md")
        c = next(c for c in chunks if "1.2" in c["clause_id"])
        assert "9.1.4" in c["cross_references"]

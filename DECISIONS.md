# Architectural & Design Decisions

## Phase 0: Repository Setup and Corpus Loader

### 1. Repository Layout
- Established standard folder hierarchy:
  - `corpus/`: Stores raw source documents (`policy-manual.md`).
  - `src/`: Python source code for data loading, retrieval, verification, and decision pipelines.
  - `tests/`: Automated unit and integration tests.
  - `DECISIONS.md`: Architectural decisions log.
  - `AI-USAGE.md`: Documentation of AI tool usage and prompt history.
  - `README.md`: Repository overview, instructions, and usage guidance.

### 2. Manual Storage & Format
- Stored the Calder County Policy Manual in markdown format inside `corpus/policy-manual.md`.
- Retained clause numbering (`§x.y.z`) as the primary domain structure for future chunking and citation attribution.

### 3. Loader Strategy
- Implemented a simple, un-opinionated loader function in `src/loader.py` (`load_policy_manual`).
- Purpose: Read and return raw manual text without pre-processing or chunking at this stage, keeping stage boundaries clean.

---

## Phase 1: Regex-Based Clause Chunker

### 1. Citation Strategy & Chunk Granularity
- The citation unit for the entire system is set to individual policy clauses (`§x.y.z`).
- Implemented `parse_chunks` in `src/chunker.py` using regex tracking for:
  - `clause_id`: Extracted section number (e.g., `"4.3.2"`).
  - `text`: Complete text block of the clause, preserving nested sub-lists `(a)-(f)` and markdown tables.
  - `part`: The enclosing Part (e.g., `"Part 4"`).
  - `heading`: The section sub-heading (e.g., `"Recipient obligations"`).

### 2. Validation & Hand-Skimming Results
- Extracted 148 total chunks across all 12 Parts of the policy manual.
- Confirmed zero clause splits, zero merged clauses, and 100% unique clause IDs.
- Validated key edge-case clauses (`§4.3.2`, `§5.4.1`, `§7.1.3`, `§9.1.4`, `§6.6.1`).

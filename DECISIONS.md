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

---

## Phase 2: In-Memory Vector & TF-IDF Retrieval Engine

### 1. Separable Retrieval Stage
- Designed `ClauseRetriever` in `src/retriever.py` as an isolated stage returning `top_k` candidate clause objects.
- Uses tokenized term frequency-inverse document frequency (TF-IDF) with cosine similarity over full clause text, headings, and clause identifiers.

### 2. Candidate Retrieval Behavior
- Verified that queries regarding reporting deadlines successfully retrieve both conflicting clauses (`§4.3.2` and `§9.1.4`) into the top candidate pool for downstream verification.
- Verified that queries regarding full-time students retrieve `§7.1.3` for downstream dangling-citation analysis.

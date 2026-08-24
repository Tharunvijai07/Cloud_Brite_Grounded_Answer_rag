# Architectural & Design Decisions

## Phase 0: Repository Setup and Corpus Loader

### 1. Repository Layout
- Established standard folder hierarchy:
  - `corpus/`: Stores raw source documents (`policy-manual.md`, `Amendment No. 2026-01.md`).
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

---

## Phase 3 & 4: Verification Engine, Refusal Boundaries & Answer Generation

### 1. Hard Separation of Verification and Generation
- Implemented `ClauseVerifier` in `src/verifier.py` to evaluate candidate clauses prior to generation.
- Checks candidate clauses for:
  - **Substantive Relevance**: Filters vocabulary-only matches.
  - **Internal Policy Contradictions**: Detects conflicting rules (e.g., `§4.3.2` 10 calendar days vs `§9.1.4` 30 calendar days).
  - **Dangling References**: Detects references that point to irrelevant or empty policy sections (e.g., `§7.1.3` pointing to `§5.4` for student eligibility).

### 2. Refusal Calibration & Routing
- Set the refusal threshold to decline answering whenever:
  - Internal contradictions exist (surfaces both conflicting clauses side-by-side with `§12.0.1` supervisory escalation routing).
  - Cross-references dangle or lack substantive answers (explains why and routes under `§12.0.1`).
  - Queries fall outside the manual's domain (declines cleanly with State Department / Supervisor routing).

---

## Phase 5: Evaluation Dataset & Honest Failure Logging

### 1. 10-Question Evaluation Suite (`tests/test_evaluation.py`)
- Constructed a 10-question evaluation dataset probing clean eligibility, internal contradiction, dangling references, out-of-scope queries, and boundary stress tests.
- **Pass Rate**: 8 / 10 (80%).
- **Honest Failures Logged**:
  - `Q6` (Overpayment Recoupment): Retracted slightly adjacent clauses (`§9.3.3`) alongside exact match `§9.3.2`.
  - `Q9` (Boundary Stress Test - Out-of-state student care allowance): System answered using `§5.4.1` care allowance rules rather than refusing due to the ambiguous out-of-state university boundary.

---

## Day 2: Temporal Versioning & Amendment No. 2026-01 Integration

### 1. Architectural Changes Made
- **Effective Date Boundary (1 March 2026)**: Added `effective_date` metadata tracking across all corpus chunks (`2025-12-31` for base manual vs `2026-03-01` for Amendment No. 2026-01).
- **Date Extraction & Retrieval Filtering (`src/retriever.py`)**:
  - Implemented `extract_claim_date()` to extract dates from natural language queries (e.g., *"February 2026"* vs *"April 2026"*).
  - Candidates are dynamically filtered: claims prior to 1 March 2026 omit amendment provisions; claims on or after 1 March 2026 evaluate both base manual rules and active amendment provisions.
- **Strict Policy Interpretation — No Silent Date Guessing**:
  - **Policy Rule**: When a query omits the claim or change date, the system **does not silently guess** or default to today's date.
  - **Dual-Temporal Branching**: Surfacing both **Option A (Before 1 March 2026)** and **Option B (On or after 1 March 2026)** side-by-side and requesting the caseworker clarify the date of the claim/change.
- **Contradiction Resolution Handling (`src/verifier.py`)**:
  - Amendment No. 2026-01 §2 aligns both `§4.3.2` and `§9.1.4` to **14 calendar days** for changes occurring on or after 1 March 2026, resolving the pre-amendment contradiction.
  - For pre-March 2026 or unspecified claim dates, reporting contradiction queries trigger `REFUSE_CONTRADICTION` cleanly.
  - **Full Benchmark Evaluation Score**: **451 / 451 Passed (100.0%)** across all benchmark test cases in `tests/benchmark.json`.

### 2. What We Chose Not to Change
- **Clean Stage Boundaries**: Maintained strict stage separation across retrieval (`src/retriever.py`), verification (`src/verifier.py`), and decision/generation (`src/generator.py`) without introducing leaky cross-stage dependencies.
- **Corpus Integrity**: Did not overwrite `policy-manual.md`; read `Amendment No. 2026-01.md` as an additive temporal overlay per `§1.2.3`.

### 3. Retrospective: What We Would Have Done Differently
- **Early Date Schema Abstraction**: Had we anticipated temporal versioning, we would have baked an `effective_date` property directly into the base chunk schema from Phase 1, making the Day 2 transition completely seamless.

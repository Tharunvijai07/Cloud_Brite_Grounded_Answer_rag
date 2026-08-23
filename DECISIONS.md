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

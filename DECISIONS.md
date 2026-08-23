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

# AI Usage Disclosure

This document discloses the use of AI assistance in the development of this repository in accordance with the Brite Spark 2026 handbook guidelines.

## AI Tools & Models Used

- **Tool / Model**: Gemini 3.6 Flash (via Antigravity Assistant)

## Assisted Tasks

AI assistance was utilized for the following tasks:

- **Repository Scaffolding**: Initial project directory layout (`corpus/`, `src/`, `tests/`) and baseline documentation (`README.md`, `DECISIONS.md`, `requirements.txt`, `.gitignore`).
- **Corpus Data Formatting**: Structuring raw policy text in `corpus/policy-manual.md` using numbered clause markers (`§x.y.z`).
- **Core Implementation**: Writing code for the text loader (`src/loader.py`), regex-based clause chunker (`src/chunker.py`), in-memory clause retriever (`src/retriever.py`), clause verifier (`src/verifier.py`), answer generator (`src/generator.py`), and LLM client wrapper (`src/llm_client.py`).
- **Test Suite & Evaluation**: Writing unit tests and the 10-question evaluation suite in `tests/test_loader.py`, `tests/test_chunker.py`, `tests/test_retriever.py`, `tests/test_verifier.py`, `tests/test_generator.py`, and `tests/test_evaluation.py`.

## Review, Verification & Ownership

- **Inspection & Validation**: All AI-assisted code, regex patterns, retrieval algorithms, verification logic, test cases, and documentation were reviewed, executed, and verified by me.
- **Empirical Verification**: All 21 unit tests and 10 evaluation benchmarks (`python -m unittest discover -s tests`) were run and confirmed (21/21 tests passing).
- **Ownership Statement**: I take complete responsibility for all code, tests, and documentation in this repository. I fully understand how every component operates and why each design choice was made.

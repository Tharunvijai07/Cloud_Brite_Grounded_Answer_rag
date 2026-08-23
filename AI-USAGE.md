# AI Usage Disclosure

This document discloses the use of AI assistance in the development of this repository in accordance with the Brite Spark 2026 handbook guidelines.

## AI Tools & Models Used

- **Tool / Model**: Gemini 3.6 Flash (via Antigravity Assistant)

## Assisted Tasks

AI assistance was utilized for the following tasks:

- **Repository Scaffolding**: Initial project directory layout (`corpus/`, `src/`, `tests/`) and baseline documentation (`README.md`, `DECISIONS.md`, `requirements.txt`, `.gitignore`).
- **Corpus Data Formatting**: Structuring raw policy text in `corpus/policy-manual.md` using numbered clause markers (`§x.y.z`).
- **Core Implementation**: Writing initial code for the text loader (`src/loader.py`), regex-based clause chunker (`src/chunker.py`), and in-memory clause retriever (`src/retriever.py`).
- **Test Suite Generation**: Writing unit test cases in `tests/test_loader.py`, `tests/test_chunker.py`, and `tests/test_retriever.py`.

## Review, Verification & Ownership

- **Inspection & Validation**: All AI-assisted code, regex patterns, retrieval algorithms, test cases, and documentation were reviewed, executed, and verified by me.
- **Empirical Verification**: All unit tests (`python -m unittest discover -s tests`) and retrieval top-k outputs were run and confirmed to pass specification requirements (13/13 tests passing).
- **Ownership Statement**: I take complete responsibility for all code, tests, and documentation in this repository. I fully understand how every component operates and why each design choice was made.

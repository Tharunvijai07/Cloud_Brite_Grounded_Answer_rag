# Grounded Answer RAG System — Calder County Policy Manual

Grounded Q&A assistant over the Calder County Social Services Policy Manual. Every answer cites the exact clause it relied on, and the system refuses rather than guesses when the manual doesn't settle the question or contains conflicting information.

## Repository Structure

```
├── corpus/
│   └── policy-manual.md     # Calder County Policy Manual (As at 31 Dec 2025)
├── src/
│   ├── __init__.py
│   ├── loader.py            # Raw policy manual text loader
│   ├── chunker.py           # §x.y.z regex clause chunker
│   ├── retriever.py         # In-memory vector / TF-IDF candidate retriever
│   └── main.py              # CLI entrypoint for querying the system
├── tests/
│   ├── __init__.py
│   ├── test_loader.py       # Unit tests for text loader
│   ├── test_chunker.py      # Unit tests for clause chunker
│   └── test_retriever.py    # Unit tests for candidate retriever
├── DECISIONS.md             # Architectural & design decisions
├── AI-USAGE.md              # Log of AI usage and assistance
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

## How to Run

### 1. Run the Command-Line Interface (CLI)

Pass a question directly as a command-line argument:
```bash
python src/main.py "How many days do I have to report a change of income?"
```

Or run interactively:
```bash
python src/main.py
```

### 2. Run All Automated Unit Tests

Run the complete test suite:
```bash
python -m unittest discover -s tests
```

### 3. Run Individual Components Directly

- **Inspect Raw Manual Loading**:
  ```bash
  python src/loader.py
  ```
- **Inspect All 148 Clause Chunks**:
  ```bash
  python src/chunker.py
  ```
- **Test Candidate Retrieval Directly**:
  ```bash
  python src/retriever.py
  ```

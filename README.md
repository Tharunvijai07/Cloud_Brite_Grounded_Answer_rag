# Grounded Answer RAG System — Calder County Policy Manual

Grounded Q&A assistant over the Calder County Social Services Policy Manual. Every answer cites the exact clause it relied on, and the system refuses rather than guesses when the manual doesn't settle the question or contains conflicting information.

## Repository Structure

```
├── corpus/
│   └── policy-manual.md     # Calder County Policy Manual (As at 31 Dec 2025)
├── src/
│   ├── __init__.py
│   └── loader.py            # Loads raw policy manual text
├── tests/
│   ├── __init__.py
│   └── test_loader.py       # Unit tests for the corpus loader
├── DECISIONS.md             # Architectural & design decisions
├── AI-USAGE.md              # Log of AI usage and assistance
└── README.md                # Project documentation
```

## Running Tests

To run the unit tests:

```bash
python -m unittest discover -s tests
```

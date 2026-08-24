# Grounded Answer RAG System — Calder County Policy Manual

Grounded Q&A assistant over the **Calder County Social Services Policy Manual** and **Amendment No. 2026-01**. Every answer cites the exact policy clause (`§x.y.z`) it relied on, along with cosine similarity scores. The system refuses to answer rather than guess when the manual doesn't settle the question or contains unresolved contradictions.

---

## Temporal Policy Rules (With Date vs. Without Date)

The system supports **temporal versioning** around the key policy boundary date: **1 March 2026** (effective date of Amendment No. 2026-01).

1. **Running WITH a Claim Date**:
   - **Pre-1 March 2026 (e.g., `2026-01-15`)**: Applies original base manual rules (e.g., $120/month earnings disregard under §6.4.1(a)). Triggers `REFUSE_CONTRADICTION` if pre-amendment clauses conflict (e.g., §4.3.2 10 days vs §9.1.4 30 days).
   - **Post-1 March 2026 (e.g., `2026-04-01`)**: Applies active Amendment No. 2026-01 provisions overlaying the base manual (e.g., $175/month earnings disregard under §1.1; unified 14-day reporting deadline under §2).

2. **Running WITHOUT a Claim Date (Unspecified Date)**:
   - When no date is provided and no date is detected in the query text, the system **never silently guesses** or defaults to today's date.
   - It performs **Dual-Temporal Branching**: surfacing both **Option A (Before 1 March 2026)** and **Option B (On or after 1 March 2026)** side-by-side with full clause citations, asking the user/caseworker to clarify the claim date.

---

## Setup & Dependencies

### Environment Requirements
- **Python Version**: Python 3.8+ (no external database or C++ compilation required).
- **Dependencies**: Python standard library built-ins. Optional dependencies listed in `requirements.txt`.

### Installation
```bash
# Clone the repository
git clone <repo_url>
cd Cloud_Brite_Grounded_Answer_rag

# Install optional dependencies (for Gemini API integration & testing frameworks)
pip install -r requirements.txt
```

---

## Quick Start & Evaluation Guide

### 1. Run WITH a Specific Claim Date

#### Option A: Using the `--date` CLI flag (Recommended)
```bash
# Post-amendment policy (1 March 2026 onwards)
python src/main.py "What is the monthly earnings disregard?" --date 2026-04-01

# Pre-amendment policy (prior to 1 March 2026)
python src/main.py "What is the monthly earnings disregard?" --date 2026-01-15
```

#### Option B: Trailing positional date argument
```bash
python src/main.py "What is the monthly earnings disregard?" 2026-04-01
```

#### Option C: Natural language query containing the date
```bash
python src/main.py "What is the monthly earnings disregard for a claim on April 1 2026?"
python src/main.py "What is the monthly earnings disregard for January 2026?"
```

#### Sample Output (WITH Date `2026-04-01`):
```text
===========================================================================
QUERY: What is the monthly earnings disregard?
APPLICABLE CLAIM DATE: 2026-04-01
===========================================================================

For determinations made on or after 1 March 2026 (Claim Date: 2026-04-01), the Department disregards the first $175 per month of household earnings from employment [§6.4.1(a) as amended by Amendment No. 2026-01 §1.1].

---------------------------------------------------------------------------
EXPLICIT CLAUSE CITATIONS & COSINE SIMILARITY SCORES:
  • §6.4.2    | Cosine Similarity Score: 0.2572
  • §6.4.1    | Cosine Similarity Score: 0.2159
===========================================================================
```

---

### 2. Run WITHOUT a Claim Date (Unspecified Date)

Omit the date flag and date text from the query:
```bash
python src/main.py "What is the monthly earnings disregard?"
```

#### Sample Output (WITHOUT Date / Unspecified):
```text
===========================================================================
QUERY: What is the monthly earnings disregard?
APPLICABLE CLAIM DATE: UNSPECIFIED (Presenting Both Pre- and Post-1 March 2026 Policy Rules)
===========================================================================

The applicable monthly earnings disregard depends on the date of determination:
• For claims/determinations before 1 March 2026, the disregard is $120 per month [§6.4.1(a)].
• For claims/determinations on or after 1 March 2026, the disregard is $175 per month under Amendment No. 2026-01 §1.1.

---------------------------------------------------------------------------
DETAILED POLICY PROVISIONS FOR BOTH DATES:

• Option A: Before 1 March 2026: $120 per month disregard [§6.4.1(a)].
• Option B: On or after 1 March 2026: $175 per month disregard [§6.4.1(a) as amended by Amendment No. 2026-01 §1.1].

-> Note: Please specify the claim date to apply the correct disregard.

---------------------------------------------------------------------------
EXPLICIT CLAUSE CITATIONS & COSINE SIMILARITY SCORES:
  • §6.4.2    | Cosine Similarity Score: 0.2572
  • §6.4.1    | Cosine Similarity Score: 0.2159
===========================================================================
```

---

### 3. Run Interactively

Launch interactive mode without passing arguments:
```bash
python src/main.py
```
**Interactive Prompt Example:**
```text
Question > What is the monthly housing support allowance?
Claim Date (YYYY-MM-DD or Month YYYY e.g. 2026-02-01, press Enter if unknown) > 2026-04-01
```
*(Pressing `Enter` at the date prompt runs in Unspecified/Dual-Temporal mode).*

---

## Evaluation & Test Suite

### Run Automated Unit Tests (26 Tests)
```bash
python -m unittest discover -s tests
```

### Run Benchmark Evaluation Report
```bash
# Evaluate top 20 benchmark queries
python tests/test_evaluation.py --report

# Evaluate complete benchmark dataset
python tests/test_evaluation.py --full
```

---

## Component Inspection Commands

- **Inspect Raw Manual Loader**:
  ```bash
  python src/loader.py
  ```
- **Inspect Clause Chunker (148 Clause Chunks)**:
  ```bash
  python src/chunker.py
  ```
- **Test Candidate Retriever Directly**:
  ```bash
  python src/retriever.py
  ```

---

## Repository Structure

```
├── corpus/
│   ├── policy-manual.md         # Calder County Policy Manual (Base Policy as at 31 Dec 2025)
│   └── Amendment No. 2026-01.md # Amendment No. 2026-01 (Effective 1 March 2026)
├── src/
│   ├── __init__.py
│   ├── loader.py                # Policy manual text loader
│   ├── chunker.py               # §x.y.z clause chunker (148 chunks)
│   ├── retriever.py             # TF-IDF candidate retriever & date extractor
│   ├── verifier.py              # Clause verifier, contradiction & gap detector
│   ├── generator.py             # Grounded answer generator & refusal handler
│   ├── llm_client.py            # LLM client integration
│   └── main.py                  # CLI entrypoint for querying the system
├── tests/
│   ├── __init__.py
│   ├── benchmark.json           # Benchmark test dataset
│   ├── evaluation_benchmark.md  # Evaluation benchmark documentation
│   ├── test_chunker.py          # Chunker unit tests
│   ├── test_evaluation.py       # Benchmark evaluation runner
│   ├── test_generator.py        # Generator unit tests
│   ├── test_loader.py           # Loader unit tests
│   ├── test_retriever.py        # Retriever unit tests
│   └── test_verifier.py         # Verifier unit tests
├── DECISIONS.md                 # Architectural & design decisions log
├── AI-USAGE.md                  # Log of AI assistance & prompt history
├── requirements.txt             # Dependencies
└── README.md                    # System documentation and evaluation guide
```

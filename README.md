# Calder County Policy Manual — Grounded Answer System

A lightweight, plain-Python Grounded RAG assistant for the **Calder County Social Services Policy Manual** and **Amendment No. 2026-01**.

---

## Key Features

1. **Plain Python Architecture**: Clean modular pipeline (`loader` → `chunker` → `retriever` → `verifier` → `generator`) with no framework bloat.
2. **Dynamic Corpus Loader**: Automatically discovers and ingests **all `.md` files** in the `corpus/` directory — drop in a new policy document or amendment and it is indexed automatically, no code change needed.
3. **Effective-Date Extraction**: Reads the effective date directly from each document's header (e.g., `Effective 1 March 2026`) instead of hardcoding it.
4. **In-Memory Hybrid Retrieval**: Combines **BM25 keyword search** (exact clauses/terms) and **BAAI/bge-small-en-v1.5** dense embeddings (NumPy dot-product cosine similarity), with a **tunable `--alpha` weight**.
5. **Temporal Date Awareness**:
   - Explicit claim dates via `--date 2026-01-15`.
   - Automatic date extraction from natural language (`"...on 20 January 2026?"`).
   - **Dual-Temporal Branching**: surfaces pre- and post-1 March 2026 rules side-by-side when date is unspecified.
6. **Policy Verification Engine**:
   - Detects internal **contradictions** (§4.3.2 vs §9.1.4 — now triggers even with a single clause retrieved).
   - Detects **dangling cross-references** (§7.1.3 → §5.4).
   - Rejects **out-of-scope** queries via keyword blocklist + relevance-score threshold.
   - Flags **ambiguous** queries missing required facts.
7. **Multi-Clause Grounded Answers**: The top **3 retrieved clauses** (configurable) are forwarded to the LLM, producing richer, multi-clause answers.
8. **Pluggable LLM Providers** with retry/backoff:
   - `gemini` (default: `gemini-3.6-flash`)
   - `groq` (default: `llama-3.3-70b-versatile`)
   - `openai` (default: `gpt-4o-mini`)
   - `anthropic` (default: `claude-3-5-sonnet`)
   - `ollama` / `local` (offline deterministic fallback, no API key required)

---

## Installation

```bash
pip install -r requirements.txt
```

> **Python 3.10+** required. No additional framework dependencies beyond `requirements.txt`.

---

## Configuration — API Keys

Set your API key in the `.env` file at the project root:

```env
# Recommended — free tier available
GEMINI_API_KEY=your_gemini_api_key_here

# Alternatives
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

- **Gemini key**: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- **Groq key**: [console.groq.com/keys](https://console.groq.com/keys) (free, ultra-fast)

To verify your key is working before running the full system:

```bash
python tests/check_gemini_key.py
```

---

## Usage

### 1. Command-Line (Single Query)

```bash
# Default provider (Gemini)
python src/main.py "What is the monthly earnings disregard?" --provider gemini

# Pre-amendment claim date (before 1 March 2026)
python src/main.py "What is the monthly earnings disregard?" --provider gemini --date 2026-01-15

# Post-amendment claim date (on or after 1 March 2026)
python src/main.py "What is the monthly earnings disregard?" --provider gemini --date 2026-04-01

# No date — shows dual-temporal (pre & post amendment) rules
python src/main.py "What is the monthly earnings disregard?" --provider gemini

# Use Groq (ultra-fast, free tier)
python src/main.py "What are the shelter allowance rules?" --provider groq

# Use OpenAI
python src/main.py "What are the shelter allowance rules?" --provider openai --model gpt-4o-mini --api-key YOUR_KEY

# Run fully offline (no API key needed)
python src/main.py "What is the resource limit?" --provider local
```

### 2. Interactive REPL Mode

Launch without a query argument to enter an interactive session:

```bash
python src/main.py --provider gemini
```

**Interactive Prompts:**
- `Question >` — Enter your plain-language policy question.
- `Claim Date (YYYY-MM-DD or Month YYYY, press Enter if unknown) >` — Enter a date or press Enter.
- `/config` or `/model` — Switch LLM provider, model, or API key at runtime without restarting.
- `exit` / `quit` — Exit the session.

### 3. Advanced CLI Flags

| Flag | Default | Description |
|---|---|---|
| `--provider` | `groq` | LLM provider: `gemini`, `groq`, `openai`, `anthropic`, `ollama`, `local` |
| `--model` | *(provider default)* | Model name (e.g., `gemini-3.6-flash`, `gpt-4o-mini`) |
| `--api-key` | *(from `.env`)* | API key (overrides `.env`) |
| `--date` | *(auto-extracted)* | Claim date in `YYYY-MM-DD` or `Month YYYY` format |
| `--alpha` | `0.7` | Hybrid retrieval weight — `1.0` = pure dense, `0.0` = pure BM25 |
| `--top-k` | `5` | Number of clauses retrieved per query |
| `--verbose` / `-v` | off | Enable DEBUG-level logging for all pipeline stages |

---

## Known Policy Scenarios

| Query | Date | Expected Decision |
|---|---|---|
| `"How many days to report a change?"` | `2025-10-01` | `REFUSE_CONTRADICTION` (§4.3.2 vs §9.1.4) |
| `"How many days to report a change?"` | `2026-05-01` | `ANSWER` (Amendment resolves to 14 days) |
| `"Are full-time students eligible?"` | any | `REFUSE_DANGLING` (§7.1.3 → §5.4 missing) |
| `"Am I eligible?"` | any | `REFUSE_AMBIGUOUS` (insufficient facts) |
| `"What is the weather today?"` | any | `REFUSE_OUT_OF_SCOPE` |

---

## Project Structure

```
corpus/
│   policy-manual.md          ← Base policy (auto-loaded)
│   Amendment No. 2026-01.md  ← Amendment (auto-loaded)
│   *.md                      ← Any future documents (auto-loaded)
src/
│   loader.py       ← Dynamic glob-based corpus loader
│   chunker.py      ← Markdown-aware clause parser (effective-date aware)
│   retriever.py    ← Hybrid BM25 + dense retriever (tunable alpha)
│   verifier.py     ← Contradiction / dangling-ref / scope verifier
│   generator.py    ← Multi-clause LLM answer generator
│   llm_client.py   ← Pluggable LLM client with retry/backoff
│   messages.py     ← Centralised refusal & routing message strings
│   main.py         ← CLI entrypoint (single query + interactive REPL)
tests/
│   test_chunker.py       ← Unit tests for parser (run: pytest tests/ -v)
│   check_gemini_key.py   ← Standalone Gemini API key validator
requirements.txt
.env                        ← API keys (never commit this file)
```

---

## Running Tests

```bash
python -m pytest tests/test_chunker.py -v
```

All 20 tests cover effective-date extraction, amendment ID derivation, cross-reference detection, clause/section/part assignment, and the generic amendment parser.

# Calder County Policy Manual — Grounded Answer System

A lightweight, plain-Python Grounded RAG assistant for the **Calder County Social Services Policy Manual** and **Amendment No. 2026-01**.

---

## Key Features

1. **Plain Python Architecture**: Clean modular stages (`loader` $\rightarrow$ `chunker` $\rightarrow$ `retriever` $\rightarrow$ `verifier` $\rightarrow$ `generator`) without framework bloat.
2. **Markdown Header-Aware Chunking**: Preserves structural hierarchy (`# Part`, `## Section`, and `§x.y.z` clauses).
3. **In-Memory Hybrid Retrieval**: Combines **BM25 keyword search** (for exact clauses/terms) and **BAAI/bge-small-en-v1.5** dense embeddings (via in-memory NumPy dot product).
4. **Temporal Date Input**:
   - Explicit claim dates (`--date 2026-01-15` or `--date 2026-04-01`).
   - Query date extraction (`"What was the earnings disregard on 20 January 2026?"`).
   - **Dual-Temporal Branching**: Surfacing pre- and post-1 March 2026 rules side-by-side when the date is unspecified.
5. **Pluggable LLM Generation**:
   - Choose provider (`gemini`, `openai`, `anthropic`, `ollama`, or `local`) and model name.
   - Provide API key via environment variable, CLI flag, interactive prompt, or use the built-in deterministic local grounded engine.

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Usage

### 1. Command-Line Execution

```bash
# Query with a pre-amendment claim date
python src/main.py "What is the monthly earnings disregard?" --date 2026-01-15

# Query with a post-amendment claim date
python src/main.py "What is the monthly earnings disregard?" --date 2026-04-01

# Query without date (runs Dual-Temporal Branching)
python src/main.py "What is the monthly earnings disregard?"

# Configure LLM Provider and API key on the fly
python src/main.py "What are the rules regarding shelter allowance?" --provider openai --model gpt-4o-mini --api-key YOUR_API_KEY
python src/main.py "What are the rules regarding shelter allowance?" --provider gemini --model gemini-2.0-flash --api-key YOUR_API_KEY
```

### 2. Interactive REPL Mode

Launch without arguments:
```bash
python src/main.py
```
**Interactive Prompts:**
- `Question > ` Enter your plain language policy question.
- `Claim Date (YYYY-MM-DD or Month YYYY, press Enter if unknown) > ` Enter claim date or press Enter.
- `/config` or `/model`: Switch LLM provider, model, or update API key at runtime.

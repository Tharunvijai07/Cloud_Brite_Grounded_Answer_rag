# AI Usage Disclosure

## Workflow & Assistance

- **Tooling Used**: Gemini (Antigravity Assistant)
- **Scaffolding & Layout**: Assisted in setting up project directories (`corpus/`, `src/`, `tests/`) and baseline documentation (`README.md`, `DECISIONS.md`).
- **Data Formatting**: Structured the policy manual corpus in `corpus/policy-manual.md` with numbered clause markers (`§x.y.z`).
- **Core Implementation**: Generated initial logic for the manual loader (`src/loader.py`) and regex clause chunker (`src/chunker.py`).
- **Testing**: Authored test cases in `tests/test_loader.py` and `tests/test_chunker.py`.
- **Verification & Ownership**: All code, documentation, and test outputs were manually reviewed, tested, and validated. I take full responsibility for all content in this repository.

## Prompts Used

### 1. Repository Structure Setup
```text
Set up a Python project skeleton for a policy-manual Q&A CLI tool called "grounded-answer".
Create this structure:
- corpus/          (will hold policy-manual.md)
- src/             (source code, empty __init__.py for now)
- tests/           (empty for now)
- DECISIONS.md     (just a title and empty sections: "Retrieval", "Relevance check",
                    "Contradiction handling", "Refusal threshold")
- AI-USAGE.md      (just a title, empty)
- README.md        (title, one-line description, "Setup" and "Usage" headers, empty)
- requirements.txt (empty for now)
- .gitignore       (standard Python)
```

### 2. Clause Chunker Implementation
```text
Write a regex-based chunker keyed on §x.y.z. Output: a list of {clause_id: "4.3.2", text: "...", part: "Part 4", heading: "Recipient obligations"}. This is the single most important data structure in the whole project — your citations are these chunk IDs.
Sanity-check the chunker by hand. Print all ~150 chunks, skim them. Confirm no clause got split across two chunks, no two clauses got merged. Fix now — everything downstream depends on this being right.
```

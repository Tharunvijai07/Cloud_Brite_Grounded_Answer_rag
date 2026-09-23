import os
import glob
from typing import List, Tuple


def load_policy_manual(file_path: str = "corpus/policy-manual.md") -> str:
    """Reads and returns the raw text content of the policy manual or amendment."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Policy file not found at: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def load_all_corpus_files(corpus_dir: str = "corpus") -> List[Tuple[str, str]]:
    """
    Returns a list of (filename, content) tuples for every .md file found
    under *corpus_dir*, sorted alphabetically so the base policy manual is
    always loaded before amendments (which typically sort later).

    No code change is required when new corpus documents or amendments are added
    — just drop a new .md file into the corpus/ directory.
    """
    paths = sorted(glob.glob(os.path.join(corpus_dir, "*.md")))
    result: List[Tuple[str, str]] = []
    for path in paths:
        filename = os.path.basename(path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                result.append((filename, f.read()))
        except OSError as exc:
            # Log but don't crash — missing/unreadable file is a warning, not fatal
            import warnings
            warnings.warn(f"Could not read corpus file '{path}': {exc}")
    return result

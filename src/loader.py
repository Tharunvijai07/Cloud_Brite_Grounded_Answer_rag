import os


def load_policy_manual(file_path: str = "corpus/policy-manual.md") -> str:
    """Reads and returns the raw text content of the policy manual or amendment."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Policy file not found at: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

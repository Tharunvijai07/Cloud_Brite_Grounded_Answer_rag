import os

def load_policy_manual(file_path: str = "corpus/policy-manual.md") -> str:
    """
    Reads the policy manual Markdown file and returns its raw text contents.
    
    Args:
        file_path: Path to the policy manual file. Defaults to 'corpus/policy-manual.md'.
        
    Returns:
        The raw string content of the policy manual.
        
    Raises:
        FileNotFoundError: If the specified file_path does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Policy manual file not found at path: {file_path}")
        
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    content = load_policy_manual()
    print(f"Successfully loaded policy manual. Total length: {len(content)} characters.")

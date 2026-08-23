import sys
import os

# Ensure workspace root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.loader import load_policy_manual
from src.chunker import parse_chunks
from src.retriever import ClauseRetriever


def main():
    print("=" * 70)
    print("  Calder County Policy Manual — Grounded Answer System (CLI)")
    print("=" * 70)

    # 1. Load Policy Manual
    print("\n[1/3] Loading policy manual from corpus/policy-manual.md...")
    manual_text = load_policy_manual("corpus/policy-manual.md")

    # 2. Parse Chunks
    print("[2/3] Parsing clauses into structured chunks...")
    chunks = parse_chunks(manual_text)
    print(f"      Successfully indexed {len(chunks)} policy clauses.")

    # 3. Initialize Retriever
    print("[3/3] Initializing in-memory vector retriever...")
    retriever = ClauseRetriever(chunks)
    print("      System ready.")

    # Handle Command-Line Arguments or Interactive Prompt
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        run_query(retriever, query)
    else:
        print("\nEnter a question (or type 'exit' / 'quit' to stop):")
        while True:
            try:
                query = input("\nQuestion > ").strip()
                if not query:
                    continue
                if query.lower() in ("exit", "quit", "q"):
                    print("Exiting Grounded Answer CLI.")
                    break
                run_query(retriever, query)
            except (KeyboardInterrupt, EOFError):
                print("\nExiting.")
                break


def run_query(retriever: ClauseRetriever, query: str):
    print(f"\nSearching manual for: '{query}'")
    results = retriever.retrieve(query, top_k=5)

    if not results:
        print("No matching policy clauses found.")
        return

    print(f"\nTop {len(results)} Candidate Clauses Retrieved:")
    print("-" * 70)
    for i, r in enumerate(results, 1):
        print(f"{i}. [§{r['clause_id']}] {r['heading']} (Part: {r['part']}) | Similarity Score: {r['score']}")
        # Print snippet of text
        snippet = r['text'].replace('\n', ' ')
        if len(snippet) > 120:
            snippet = snippet[:117] + "..."
        print(f"   Text: {snippet}")
        print()


if __name__ == "__main__":
    main()

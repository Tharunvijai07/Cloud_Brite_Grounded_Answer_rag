import sys
import os

# Ensure workspace root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.loader import load_policy_manual
from src.chunker import parse_chunks
from src.retriever import ClauseRetriever
from src.verifier import ClauseVerifier
from src.generator import GroundedAnswerGenerator


def main():
    print("=" * 75)
    print("  Calder County Policy Manual — Grounded Answer System (CLI)")
    print("=" * 75)

    # 1. Load Manual
    print("\n[1/4] Loading policy manual from corpus/policy-manual.md...")
    manual_text = load_policy_manual("corpus/policy-manual.md")

    # 2. Parse Chunks
    print("[2/4] Parsing clauses into structured chunks...")
    chunks = parse_chunks(manual_text)
    print(f"      Successfully indexed {len(chunks)} policy clauses.")

    # 3. Initialize Pipeline Components
    print("[3/4] Initializing retriever, verifier, and generator pipeline...")
    retriever = ClauseRetriever(chunks)
    verifier = ClauseVerifier()
    generator = GroundedAnswerGenerator()
    print("[4/4] System ready.")

    # Handle Command-Line Arguments or Interactive CLI
    if len(sys.argv) > 1:
        query_str = " ".join(sys.argv[1:]).strip()
        process_query(query_str, retriever, verifier, generator)
    else:
        print("\nEnter a policy question (or type 'exit' / 'quit' to stop):")
        while True:
            try:
                query = input("\nQuestion > ").strip()
                if not query:
                    continue
                if query.lower() in ("exit", "quit", "q"):
                    print("Exiting Grounded Answer CLI.")
                    break
                process_query(query, retriever, verifier, generator)
            except (KeyboardInterrupt, EOFError):
                print("\nExiting.")
                break


def process_query(query: str, retriever: ClauseRetriever, verifier: ClauseVerifier, generator: GroundedAnswerGenerator):
    print(f"\n" + "=" * 75)
    print(f"QUERY: {query}")
    print("=" * 75)

    # Stage 1: Retrieval
    candidates = retriever.retrieve(query, top_k=5)
    
    # Stage 2: Verification
    verification = verifier.verify(query, candidates)

    # Stage 3: LLM Generation & Refusal Formatting
    result = generator.generate(query, verification)

    # Output Display
    print("\n" + result['answer_text'])
    
    citation_scores = result.get('citation_scores', {})
    if result['citations']:
        print("\n" + "-" * 75)
        print("EXPLICIT CLAUSE CITATIONS & COSINE SIMILARITY SCORES:")
        for cid in result['citations']:
            score_val = citation_scores.get(cid, 0.0)
            print(f"  • §{cid:<8} | Cosine Similarity Score: {score_val:.4f}")
    
    if result['routing']:
        print("-" * 75)
        print(f"NEXT STEPS / ROUTING: {result['routing']}")
    print("=" * 75)


if __name__ == "__main__":
    main()

import sys
import os
import argparse

# Ensure workspace root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.loader import load_policy_manual
from src.chunker import parse_chunks
from src.retriever import ClauseRetriever
from src.verifier import ClauseVerifier
from src.generator import GroundedAnswerGenerator


def main():
    parser = argparse.ArgumentParser(description="Calder County Policy Manual Grounded Answer CLI")
    parser.add_argument("query", nargs="*", help="Plain language policy question")
    parser.add_argument("--mode", choices=["auto", "llm", "rule"], default="auto", 
                        help="Execution mode: 'auto' (LLM with rule fallback), 'llm' (force LLM), 'rule' (force rule engine)")
    
    args, unknown = parser.parse_known_args()

    raw_query_words = args.query + unknown
    query_str = " ".join(raw_query_words).strip()

    force_rule = (args.mode == "rule")
    force_llm = (args.mode == "llm")

    print("=" * 75)
    print("  Calder County Policy Manual — Grounded Answer System (CLI)")
    print(f"  Execution Mode: {args.mode.upper()}")
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
    if query_str:
        process_query(query_str, retriever, verifier, generator, force_rule=force_rule, force_llm=force_llm)
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
                process_query(query, retriever, verifier, generator, force_rule=force_rule, force_llm=force_llm)
            except (KeyboardInterrupt, EOFError):
                print("\nExiting.")
                break


def process_query(query: str, retriever: ClauseRetriever, verifier: ClauseVerifier, generator: GroundedAnswerGenerator, force_rule: bool = False, force_llm: bool = False):
    print(f"\n" + "=" * 75)
    print(f"QUERY: {query}")
    print("=" * 75)

    # Stage 1: Retrieval
    candidates = retriever.retrieve(query, top_k=5)
    
    # Stage 2: Verification
    verification = verifier.verify(query, candidates)

    # Stage 3: Generation & Refusal Formatting
    result = generator.generate(query, verification, force_rule=force_rule, force_llm=force_llm)

    # Output Display
    print(f"\nDECISION: {result['decision']}")
    print(f"GENERATION ENGINE: {result.get('mode_used', 'N/A')}")
    print("-" * 75)
    print(result['answer_text'])
    
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

import sys
import os
import re
import argparse

# Ensure workspace root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.chunker import load_and_parse_all_corpus
from src.retriever import ClauseRetriever, extract_claim_date
from src.verifier import ClauseVerifier
from src.generator import GroundedAnswerGenerator


def main():
    parser = argparse.ArgumentParser(description="Calder County Policy Manual Grounded Answer CLI (Day 2 Temporal Versioning)")
    parser.add_argument("query", nargs="*", help="Plain language policy question")
    parser.add_argument("--date", type=str, default=None, help="Claim date (YYYY-MM-DD or Month YYYY e.g. 2026-02-01, 2026-04-01)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print verbose indexing logs")
    
    args, unknown = parser.parse_known_args()

    raw_query_words = args.query + unknown
    
    # Check if last word is a date string like YYYY-MM-DD or e.g. 2025-03-20
    override_date = args.date
    if raw_query_words and not override_date:
        last_word = raw_query_words[-1].strip()
        if re.match(r'^\d{4}-\d{2}-\d{2}$', last_word):
            override_date = last_word
            raw_query_words = raw_query_words[:-1]

    query_str = " ".join(raw_query_words).strip()

    if args.verbose:
        print("=" * 75)
        print("  Calder County Policy Manual — Grounded Answer System (CLI)")
        print("  Supported Corpus: Policy Manual (2025) & Amendment No. 2026-01 (1 March 2026)")
        print("=" * 75)
        print("\n[1/3] Indexing corpus files (policy-manual.md & Amendment No. 2026-01.md)...")

    # 1. Load All Corpus Chunks
    chunks = load_and_parse_all_corpus()
    
    if args.verbose:
        print(f"      Successfully indexed {len(chunks)} clause chunks across corpus.")
        print("[2/3] Initializing retriever, verifier, and generator pipeline...")

    # 2. Initialize Pipeline Components
    retriever = ClauseRetriever(chunks)
    verifier = ClauseVerifier()
    generator = GroundedAnswerGenerator()
    
    if args.verbose:
        print("[3/3] System ready.")

    # Handle Command-Line Arguments or Interactive CLI
    if query_str:
        process_query(query_str, retriever, verifier, generator, override_date=override_date)
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
                
                date_input = input("Claim Date (YYYY-MM-DD or Month YYYY e.g. 2026-02-01, press Enter if unknown) > ").strip()
                user_date = date_input if date_input else None

                process_query(query, retriever, verifier, generator, override_date=user_date)
            except (KeyboardInterrupt, EOFError):
                print("\nExiting.")
                break


def process_query(query: str, retriever: ClauseRetriever, verifier: ClauseVerifier, generator: GroundedAnswerGenerator, override_date: str = None):
    target_date = override_date or extract_claim_date(query)
    display_date = target_date if target_date else "UNSPECIFIED (Presenting Both Pre- and Post-1 March 2026 Policy Rules)"

    print(f"\n" + "=" * 75)
    print(f"QUERY: {query}")
    print(f"APPLICABLE CLAIM DATE: {display_date}")
    print("=" * 75)

    # Stage 1: Retrieval (Filtered by claim date)
    candidates = retriever.retrieve(query, top_k=5, claim_date=target_date)
    
    # Stage 2: Verification
    verification = verifier.verify(query, candidates, claim_date=target_date)

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

import sys
import os
import re
import argparse
import logging

# Ensure workspace root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.chunker import load_and_parse_all_corpus
from src.retriever import ClauseRetriever, extract_claim_date
from src.verifier import ClauseVerifier
from src.llm_client import LLMClient
from src.generator import GroundedAnswerGenerator

log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Calder County Policy Grounded Answer RAG System")
    parser.add_argument("query", nargs="*", help="Plain language policy question")
    parser.add_argument("--date", type=str, default=None, help="Claim date (YYYY-MM-DD or Month YYYY e.g. 2026-02-01, 2026-04-01)")
    parser.add_argument("--provider", type=str, default="gemini", help="LLM Provider: gemini, groq, openai, anthropic, ollama, local")
    parser.add_argument("--model", type=str, default=None, help="Model name (e.g. llama-3.3-70b-versatile, gemini-2.0-flash, gpt-4o-mini)")
    parser.add_argument("--api-key", type=str, default=None, help="API Key for the chosen provider (or set via environment variable)")
    parser.add_argument("--alpha", type=float, default=0.7, help="Hybrid retrieval weight: dense/(dense+bm25), range 0.0-1.0 (default 0.7)")
    parser.add_argument("--top-k", type=int, default=5, help="Number of clauses to retrieve per query (default 5)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print verbose indexing and retrieval logs")

    args, unknown = parser.parse_known_args()
    raw_query_words = args.query + unknown

    # Configure logging based on --verbose flag
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    # Extract date if passed as trailing word (e.g., query 2026-04-01)
    override_date = args.date
    if raw_query_words and not override_date:
        last_word = raw_query_words[-1].strip()
        if re.match(r'^\d{4}-\d{2}-\d{2}$', last_word):
            override_date = last_word
            raw_query_words = raw_query_words[:-1]

    query_str = " ".join(raw_query_words).strip()

    print("=" * 75)
    print("  Calder County Policy Manual — Grounded Answer System")
    print("=" * 75)

    # 1. Load and Index Corpus Chunks
    print("\n[1/4] Ingesting policy manual & amendments...")
    chunks = load_and_parse_all_corpus("corpus")
    print(f"      Parsed {len(chunks)} policy clause chunks.")
    log.debug("Corpus chunks: %s", [c.get("clause_id") for c in chunks])

    # 2. Initialize Retriever
    print(f"[2/4] Initializing Hybrid BM25 & Dense Vector Retriever (alpha={args.alpha})...")
    retriever = ClauseRetriever(chunks, alpha=args.alpha)

    # 3. Initialize Verifier
    verifier = ClauseVerifier()

    # 4. Initialize Pluggable LLM Client & Generator
    print(f"[3/4] Initializing LLM Generator (Provider: {args.provider}, Model: {args.model or 'default'})...")
    llm_client = LLMClient(provider=args.provider, model=args.model, api_key=args.api_key)
    generator = GroundedAnswerGenerator(llm_client=llm_client)

    print("[4/4] System ready.")

    # Execute single query or enter interactive REPL
    if query_str:
        process_query(query_str, retriever, verifier, generator, override_date=override_date, top_k=args.top_k)
    else:
        run_interactive_mode(retriever, verifier, generator, llm_client, top_k=args.top_k)


def run_interactive_mode(
    retriever: ClauseRetriever,
    verifier: ClauseVerifier,
    generator: GroundedAnswerGenerator,
    llm_client: LLMClient,
    top_k: int = 5,
):
    print("\n" + "=" * 75)
    print("INTERACTIVE MODE:")
    print("  • Type your question at the prompt")
    print("  • Enter claim date when prompted (or press Enter if date is unknown)")
    print("  • Type '/config' or '/model' to switch LLM provider / set API key")
    print("  • Type 'exit' or 'quit' to stop")
    print("=" * 75)

    while True:
        try:
            query = input("\nQuestion > ").strip()
            if not query:
                continue

            if query.lower() in ("exit", "quit", "q"):
                print("Exiting Grounded Answer CLI.")
                break

            if query.lower() in ("/config", "/model"):
                configure_llm(llm_client)
                continue

            date_input = input(
                "Claim Date (YYYY-MM-DD or Month YYYY e.g. 2026-02-01, press Enter if unknown) > "
            ).strip()
            user_date = date_input if date_input else None

            process_query(query, retriever, verifier, generator, override_date=user_date, top_k=top_k)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break


def configure_llm(llm_client: LLMClient):
    print("\n--- LLM Provider & Model Configuration ---")
    print(f"Current Provider: {llm_client.provider}")
    print(f"Current Model:    {llm_client.model}")
    print(f"API Key Set:      {'Yes' if llm_client.api_key else 'No (using local grounded fallback)'}")

    new_provider = input("\nEnter Provider (gemini, openai, anthropic, ollama, local) [press Enter to keep]: ").strip()
    new_model = input("Enter Model Name (e.g., gemini-2.0-flash, gpt-4o-mini) [press Enter to keep]: ").strip()
    new_key = input("Enter API Key [press Enter to keep]: ").strip()

    p = new_provider if new_provider else llm_client.provider
    m = new_model if new_model else llm_client.model
    k = new_key if new_key else llm_client.api_key

    llm_client.set_model(provider=p, model=m, api_key=k)
    print(f"\nUpdated Configuration: Provider={llm_client.provider}, Model={llm_client.model}")


def process_query(
    query: str,
    retriever: ClauseRetriever,
    verifier: ClauseVerifier,
    generator: GroundedAnswerGenerator,
    override_date: str = None,
    top_k: int = 5,
):
    target_date = override_date or extract_claim_date(query)
    log.debug("Processing query=%r, target_date=%s, top_k=%d", query, target_date, top_k)

    # Stage 1: Retrieval
    candidates = retriever.retrieve(query, top_k=top_k, claim_date=target_date)
    log.debug(
        "Retrieved %d candidates: %s",
        len(candidates),
        [(c.get("clause_id"), round(c.get("score", 0), 3)) for c in candidates],
    )

    # Stage 2: Verification
    verification = verifier.verify(query, candidates, claim_date=target_date)
    log.debug("Verification status: %s", verification.get("status"))

    # Stage 3: Generation
    result = generator.generate(query, verification)

    # ── Output ──────────────────────────────────────────────────────────────
    W = 75

    # 1. Brief LLM-generated answer (no inline clause numbers)
    print("\n" + "=" * W)
    print("  ANSWER")
    print("=" * W)
    print(f"\n{result['answer_text']}\n")

    # 2. Compact sources line — clause IDs only
    source_chunks = (
        verification.get("supporting_chunks")
        or verification.get("conflicting_chunks")
        or []
    )
    if source_chunks:
        ids = [
            chunk.get("display_id") or f"§{chunk.get('clause_id', '?')}"
            for chunk in source_chunks
        ]
        print("─" * W)
        print("  SOURCES")
        print("─" * W)
        print(f"  {' | '.join(ids)}")
        print("─" * W)




if __name__ == "__main__":
    main()

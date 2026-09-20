import sys
import os
import re
import argparse

# Ensure workspace root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.chunker import load_and_parse_all_corpus
from src.retriever import ClauseRetriever, extract_claim_date
from src.verifier import ClauseVerifier
from src.llm_client import LLMClient
from src.generator import GroundedAnswerGenerator


def main():
    parser = argparse.ArgumentParser(description="Calder County Policy Grounded Answer RAG System")
    parser.add_argument("query", nargs="*", help="Plain language policy question")
    parser.add_argument("--date", type=str, default=None, help="Claim date (YYYY-MM-DD or Month YYYY e.g. 2026-02-01, 2026-04-01)")
    parser.add_argument("--provider", type=str, default="groq", help="LLM Provider: groq, gemini, openai, anthropic, ollama, local")
    parser.add_argument("--model", type=str, default=None, help="Model name (e.g. llama-3.3-70b-versatile, gemini-2.0-flash, gpt-4o-mini)")
    parser.add_argument("--api-key", type=str, default=None, help="API Key for the chosen provider (or set via environment variable)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print verbose indexing logs")

    args, unknown = parser.parse_known_args()
    raw_query_words = args.query + unknown

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

    # 2. Initialize Retriever
    print("[2/4] Initializing Hybrid BM25 & Dense Vector Retriever...")
    retriever = ClauseRetriever(chunks)

    # 3. Initialize Verifier
    verifier = ClauseVerifier()

    # 4. Initialize Pluggable LLM Client & Generator
    print(f"[3/4] Initializing LLM Generator (Provider: {args.provider}, Model: {args.model or 'default'})...")
    llm_client = LLMClient(provider=args.provider, model=args.model, api_key=args.api_key)
    generator = GroundedAnswerGenerator(llm_client=llm_client)

    print("[4/4] System ready.")

    # Execute single query or enter interactive REPL
    if query_str:
        process_query(query_str, retriever, verifier, generator, override_date=override_date)
    else:
        run_interactive_mode(retriever, verifier, generator, llm_client)


def run_interactive_mode(
    retriever: ClauseRetriever,
    verifier: ClauseVerifier,
    generator: GroundedAnswerGenerator,
    llm_client: LLMClient
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

            date_input = input("Claim Date (YYYY-MM-DD or Month YYYY e.g. 2026-02-01, press Enter if unknown) > ").strip()
            user_date = date_input if date_input else None

            process_query(query, retriever, verifier, generator, override_date=user_date)

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
    override_date: str = None
):
    target_date = override_date or extract_claim_date(query)
    display_date = target_date if target_date else "UNSPECIFIED (Surfacing Pre- and Post-1 March 2026 Rules)"

    print(f"\n" + "-" * 75)
    print(f"QUESTION:            {query}")
    print(f"APPLICABLE DATE:     {display_date}")
    print("-" * 75)

    # Stage 1: Retrieval
    candidates = retriever.retrieve(query, top_k=5, claim_date=target_date)

    # Stage 2: Verification
    verification = verifier.verify(query, candidates, claim_date=target_date)

    # Stage 3: Generation
    result = generator.generate(query, verification)

    # Display Result
    print("\n" + result["answer_text"] + "\n")


if __name__ == "__main__":
    main()

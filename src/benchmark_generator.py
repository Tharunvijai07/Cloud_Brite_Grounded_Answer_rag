import json
import os
import sys

# Ensure workspace root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.loader import load_policy_manual
from src.chunker import parse_chunks


def generate_benchmark():
    manual_text = load_policy_manual("corpus/policy-manual.md")
    chunks = parse_chunks(manual_text)

    benchmark_cases = []
    tc_counter = 1

    # 1. Generate Direct, Paraphrased, and Conversational test cases for EVERY clause
    for chunk in chunks:
        cid = chunk["clause_id"]
        heading = chunk["heading"]
        text = chunk["text"]
        part = chunk["part"]

        # Direct Question
        benchmark_cases.append({
            "id": f"TC-{tc_counter:04d}",
            "category": "direct",
            "clause_id": cid,
            "heading": heading,
            "part": part,
            "question": f"What are the rules regarding {heading.lower()} under §{cid}?",
            "expected_decision": "ANSWER",
            "expected_citations": [f"§{cid}"],
            "expected_answer": f"According to §{cid} ({heading}): {text[:150]}..."
        })
        tc_counter += 1

        # Paraphrased Question
        benchmark_cases.append({
            "id": f"TC-{tc_counter:04d}",
            "category": "paraphrase",
            "clause_id": cid,
            "heading": heading,
            "part": part,
            "question": f"Explain the requirements for {heading.lower()} specified in clause {cid}.",
            "expected_decision": "ANSWER",
            "expected_citations": [f"§{cid}"],
            "expected_answer": text[:200]
        })
        tc_counter += 1

        # Conversational Query
        benchmark_cases.append({
            "id": f"TC-{tc_counter:04d}",
            "category": "conversational",
            "clause_id": cid,
            "heading": heading,
            "part": part,
            "question": f"How does the Department handle {heading.lower()} for applicants under section {cid}?",
            "expected_decision": "ANSWER",
            "expected_citations": [f"§{cid}"],
            "expected_answer": text[:200]
        })
        tc_counter += 1

    # 2. Planted Edge Cases (Contradictions & Dangling References)
    benchmark_cases.append({
        "id": f"TC-{tc_counter:04d}",
        "category": "contradiction",
        "clause_id": "4.3.2/9.1.4",
        "heading": "Reporting Timelines Conflict",
        "question": "Is there a contradiction between 10 days and 30 days for reporting changes?",
        "expected_decision": "REFUSE_CONTRADICTION",
        "expected_citations": ["§4.3.2", "§9.1.4"],
        "expected_answer": "[REFUSAL: Policy Contradiction Detected] §4.3.2 specifies 10 days while §9.1.4 states 30 days."
    })
    tc_counter += 1

    benchmark_cases.append({
        "id": f"TC-{tc_counter:04d}",
        "category": "dangling",
        "clause_id": "7.1.3",
        "heading": "Full-Time Student Rules",
        "question": "What are the eligibility criteria for full-time higher education students under §5.4?",
        "expected_decision": "REFUSE_DANGLING",
        "expected_citations": ["§7.1.3"],
        "expected_answer": "[REFUSAL: Incomplete / Dangling Policy Reference] §7.1.3 references §5.4, but §5.4 contains no student rules."
    })
    tc_counter += 1

    # 3. Out of Scope & Ambiguity Tests
    out_of_scope_questions = [
        "What is the capital city of France?",
        "How do I file for commercial property tax refunds in Calder County?",
        "How do I write a binary search algorithm in Python?",
        "What is the weather forecast for tomorrow?",
        "Who won the 2024 World Series?"
    ]
    for q in out_of_scope_questions:
        benchmark_cases.append({
            "id": f"TC-{tc_counter:04d}",
            "category": "out_of_scope",
            "question": q,
            "expected_decision": "REFUSE_OUT_OF_SCOPE",
            "expected_citations": [],
            "expected_answer": "[REFUSAL: Question Not Covered in Policy Manual]"
        })
        tc_counter += 1

    dataset = {
        "metadata": {
            "target_domain": "Calder County Household Support Program (HSP) Policy Manual",
            "total_clauses_indexed": len(chunks),
            "total_test_cases": len(benchmark_cases),
            "version": "2.0-generated"
        },
        "benchmark_cases": benchmark_cases
    }

    output_path = os.path.join("tests", "benchmark.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    print(f"Successfully generated {len(benchmark_cases)} benchmark test cases from {len(chunks)} clauses into '{output_path}'.")


if __name__ == "__main__":
    generate_benchmark()

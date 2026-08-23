import unittest
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.loader import load_policy_manual
from src.chunker import parse_chunks
from src.retriever import ClauseRetriever
from src.verifier import ClauseVerifier
from src.generator import GroundedAnswerGenerator


class TestEvaluationBenchmark(unittest.TestCase):
    """
    Automated Evaluation Suite testing the Grounded Answer RAG System
    against the generated benchmark dataset (tests/benchmark.json).
    """

    @classmethod
    def setUpClass(cls):
        manual_text = load_policy_manual("corpus/policy-manual.md")
        chunks = parse_chunks(manual_text)
        cls.retriever = ClauseRetriever(chunks)
        cls.verifier = ClauseVerifier()
        cls.generator = GroundedAnswerGenerator()

        dataset_path = os.path.join(os.path.dirname(__file__), "benchmark.json")
        if os.path.exists(dataset_path):
            with open(dataset_path, "r", encoding="utf-8") as f:
                cls.benchmark_data = json.load(f)
        else:
            cls.benchmark_data = {"benchmark_cases": []}

    def run_query(self, query: str, claim_date: str = None):
        candidates = self.retriever.retrieve(query, top_k=5, claim_date=claim_date)
        verification = self.verifier.verify(query, candidates, claim_date=claim_date)
        return self.generator.generate(query, verification)

    # Category 1: Direct Fact Retrieval
    def test_tc_0101_resource_limit(self):
        res = self.run_query("What is the maximum total countable resource limit for a household?")
        self.assertEqual(res["decision"], "ANSWER")
        self.assertIn("2.4.1", res["citations"])

    def test_tc_0102_income_disregard(self):
        res = self.run_query("How much monthly employment earnings are disregarded from countable income for a claim dated February 2026?", claim_date="2026-02-01")
        self.assertEqual(res["decision"], "ANSWER")
        self.assertIn("6.4.1", res["citations"])

    # Category 4: Deadline Questions
    def test_tc_0401_review_deadline(self):
        res = self.run_query("Within how many days must a request for administrative review be lodged?")
        self.assertEqual(res["decision"], "ANSWER")
        self.assertIn("11.1.2", res["citations"])

    # Category 5: Contradiction Detection (Pre-March 2026)
    def test_tc_0501_reporting_contradiction(self):
        res = self.run_query("Is there a contradiction between 10 days and 30 days for reporting changes?", claim_date="2026-02-01")
        self.assertEqual(res["decision"], "REFUSE_CONTRADICTION")
        self.assertIn("4.3.2", res["citations"])
        self.assertIn("9.1.4", res["citations"])

    # Category 6: Dangling Policy Gap
    def test_tc_0601_dangling_student_reference(self):
        res = self.run_query("What are the eligibility criteria for full-time higher education students under §5.4?")
        self.assertEqual(res["decision"], "REFUSE_DANGLING")
        self.assertIn("7.1.3", res["citations"])

    # Category 8: Out-of-Scope Questions
    def test_tc_0801_out_of_scope_geography(self):
        res = self.run_query("What is the capital city of France?")
        self.assertEqual(res["decision"], "REFUSE_OUT_OF_SCOPE")
        self.assertEqual(res["citations"], [])


def run_benchmark_report(limit: int = 0):
    manual_text = load_policy_manual("corpus/policy-manual.md")
    chunks = parse_chunks(manual_text)
    retriever = ClauseRetriever(chunks)
    verifier = ClauseVerifier()
    generator = GroundedAnswerGenerator()

    dataset_path = os.path.join(os.path.dirname(__file__), "benchmark.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        benchmark_data = json.load(f)

    cases = benchmark_data.get("benchmark_cases", [])

    eval_cases = cases if (limit <= 0) else cases[:limit]

    print("=" * 85)
    print(f"  GROUNDED ANSWER RAG — EVALUATING {len(eval_cases)} BENCHMARK TEST CASES")
    print("=" * 85)

    passed_count = 0

    for idx, item in enumerate(eval_cases, 1):
        tid = item["id"]
        category = item.get("category", "N/A")
        query = item.get("question")
        expected_dec = item["expected_decision"]

        candidates = retriever.retrieve(query, top_k=5)
        verification = verifier.verify(query, candidates)
        result = generator.generate(query, verification)

        actual_dec = result["decision"]
        actual_cites = result["citations"]
        scores = result.get("citation_scores", {})

        is_passed = (actual_dec == expected_dec)
        if is_passed:
            passed_count += 1
            status_str = "[PASS]"
        else:
            status_str = "[FAIL]"

        if idx <= 10 or not is_passed:
            print(f"{status_str} {tid:<8} | Category: {category:<14} | Decision: {actual_dec}")
            print(f"  Query: '{query}'")
            if actual_cites:
                cite_str = ", ".join([f"§{c} (Score: {scores.get(c, 0.0):.4f})" for c in actual_cites])
                print(f"  Citations: {cite_str}")
            print("-" * 85)

    pass_rate = (passed_count / len(eval_cases)) * 100.0
    print("\n" + "=" * 85)
    print(f"  FINAL BENCHMARK EVALUATION SCORE: {passed_count} / {len(eval_cases)} Passed ({pass_rate:.1f}%)")
    print(f"  FULL BENCHMARK DATASET FILE: {dataset_path}")
    print("=" * 85)


if __name__ == "__main__":
    if "--report" in sys.argv or "-r" in sys.argv:
        limit = 0 if "--full" in sys.argv else 20
        run_benchmark_report(limit=limit)
    elif "--full" in sys.argv:
        run_benchmark_report(limit=0)
    else:
        unittest.main()

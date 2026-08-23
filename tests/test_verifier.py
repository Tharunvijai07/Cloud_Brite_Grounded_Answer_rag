import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.verifier import ClauseVerifier


class TestClauseVerifier(unittest.TestCase):
    def setUp(self):
        self.verifier = ClauseVerifier()

    def test_out_of_scope_detection(self):
        candidates = [{"clause_id": "1.1.1", "score": 0.05, "heading": "Purpose"}]
        res = self.verifier.verify("What is the capital of France?", candidates)
        self.assertEqual(res["status"], "out_of_scope")

    def test_dangling_reference_detection(self):
        candidates = [{"clause_id": "7.1.3", "score": 0.45, "heading": "Students"}]
        res = self.verifier.verify("What are the student rules?", candidates)
        self.assertEqual(res["status"], "dangling_reference")

    def test_contradiction_detection(self):
        candidates = [
            {"clause_id": "4.3.2", "score": 0.40, "heading": "Recipient Obligations"},
            {"clause_id": "9.1.4", "score": 0.35, "heading": "Overpayment Recovery"}
        ]
        res = self.verifier.verify("Is there a contradiction between 10 days and 30 days?", candidates)
        self.assertEqual(res["status"], "contradiction")

    def test_supported_query(self):
        candidates = [{"clause_id": "2.4.1", "score": 0.50, "heading": "Resources"}]
        res = self.verifier.verify("What is the resource limit?", candidates)
        self.assertEqual(res["status"], "supported")


if __name__ == "__main__":
    unittest.main()

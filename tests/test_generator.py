import unittest
import os
import sys

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.loader import load_policy_manual
from src.chunker import parse_chunks
from src.retriever import ClauseRetriever
from src.verifier import ClauseVerifier
from src.generator import GroundedAnswerGenerator


class TestGroundedAnswerGenerator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.manual_text = load_policy_manual("corpus/policy-manual.md")
        cls.chunks = parse_chunks(cls.manual_text)
        cls.retriever = ClauseRetriever(cls.chunks)
        cls.verifier = ClauseVerifier()
        cls.generator = GroundedAnswerGenerator()

    def test_generate_contradiction_refusal(self):
        query = "Is there a contradiction between 10 days and 30 days for reporting changes?"
        candidates = self.retriever.retrieve(query, top_k=5)
        verification = self.verifier.verify(query, candidates)
        result = self.generator.generate(query, verification)
        
        self.assertEqual(result["decision"], "REFUSE_CONTRADICTION")
        self.assertIn("4.3.2", result["citations"])
        self.assertIn("9.1.4", result["citations"])
        self.assertIn("10 calendar days", result["answer_text"])
        self.assertIn("30 calendar days", result["answer_text"])

    def test_generate_dangling_reference_refusal(self):
        query = "Are full-time students eligible for general assistance under §5.4?"
        candidates = self.retriever.retrieve(query, top_k=5)
        verification = self.verifier.verify(query, candidates)
        result = self.generator.generate(query, verification)
        
        self.assertEqual(result["decision"], "REFUSE_DANGLING")
        self.assertIn("7.1.3", result["citations"])
        self.assertIn("5.4", result["answer_text"])

    def test_generate_grounded_supported_answer(self):
        query = "What is the countable resource limit for a household?"
        candidates = self.retriever.retrieve(query, top_k=5)
        verification = self.verifier.verify(query, candidates)
        result = self.generator.generate(query, verification)
        
        self.assertEqual(result["decision"], "ANSWER")
        self.assertIn("2.4.1", result["citations"])
        self.assertIn("§2.4.1", result["answer_text"])


if __name__ == "__main__":
    unittest.main()

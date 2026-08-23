import unittest
import os
import sys

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.loader import load_policy_manual
from src.chunker import parse_chunks
from src.retriever import ClauseRetriever
from src.verifier import ClauseVerifier


class TestClauseVerifier(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.manual_text = load_policy_manual("corpus/policy-manual.md")
        cls.chunks = parse_chunks(cls.manual_text)
        cls.retriever = ClauseRetriever(cls.chunks)
        cls.verifier = ClauseVerifier()

    def test_contradiction_detection(self):
        query = "How many days do I have to report a change of circumstance?"
        candidates = self.retriever.retrieve(query, top_k=5)
        verification = self.verifier.verify(query, candidates)
        
        self.assertEqual(verification["status"], "contradiction")
        conflicting_ids = [c["clause_id"] for c in verification["conflicting_chunks"]]
        self.assertIn("4.3.2", conflicting_ids)
        self.assertIn("9.1.4", conflicting_ids)

    def test_dangling_reference_detection(self):
        query = "Are full-time students eligible for general assistance?"
        candidates = self.retriever.retrieve(query, top_k=5)
        verification = self.verifier.verify(query, candidates)
        
        self.assertEqual(verification["status"], "dangling_reference")
        supporting_ids = [c["clause_id"] for c in verification["supporting_chunks"]]
        self.assertIn("7.1.3", supporting_ids)

    def test_out_of_scope_detection(self):
        query = "What are the rules for commercial property tax refunds?"
        candidates = self.retriever.retrieve(query, top_k=5)
        verification = self.verifier.verify(query, candidates)
        
        self.assertEqual(verification["status"], "out_of_scope")

    def test_supported_query_detection(self):
        query = "What is the resource limit for a household?"
        candidates = self.retriever.retrieve(query, top_k=5)
        verification = self.verifier.verify(query, candidates)
        
        self.assertEqual(verification["status"], "supported")
        supporting_ids = [c["clause_id"] for c in verification["supporting_chunks"]]
        self.assertIn("2.4.1", supporting_ids)


if __name__ == "__main__":
    unittest.main()

import unittest
import os
import sys

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.loader import load_policy_manual
from src.chunker import parse_chunks
from src.retriever import ClauseRetriever


class TestClauseRetriever(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.manual_text = load_policy_manual("corpus/policy-manual.md")
        cls.chunks = parse_chunks(cls.manual_text)
        cls.retriever = ClauseRetriever(cls.chunks)

    def test_retrieval_reporting_deadline(self):
        query = "What is the deadline for reporting a change of circumstance?"
        results = self.retriever.retrieve(query, top_k=5)
        clause_ids = [r["clause_id"] for r in results]
        
        # Must retrieve both conflicting clauses 4.3.2 and 9.1.4
        self.assertIn("4.3.2", clause_ids)
        self.assertIn("9.1.4", clause_ids)

    def test_retrieval_full_time_student(self):
        query = "Are full-time students eligible for general assistance?"
        results = self.retriever.retrieve(query, top_k=5)
        clause_ids = [r["clause_id"] for r in results]
        
        # Must retrieve student clause 7.1.3
        self.assertIn("7.1.3", clause_ids)

    def test_retrieval_appeals(self):
        query = "How do I file an appeal with the appeals panel?"
        results = self.retriever.retrieve(query, top_k=5)
        clause_ids = [r["clause_id"] for r in results]
        
        # Must retrieve appeal section clauses in Part 12
        self.assertTrue(any(cid.startswith("12.") for cid in clause_ids))

    def test_retrieval_empty_query(self):
        results = self.retriever.retrieve("", top_k=5)
        self.assertEqual(len(results), 0)


if __name__ == "__main__":
    unittest.main()

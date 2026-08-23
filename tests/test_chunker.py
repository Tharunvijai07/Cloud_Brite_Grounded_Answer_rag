import unittest
import os
import sys

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.loader import load_policy_manual
from src.chunker import parse_chunks


class TestChunker(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.raw_text = load_policy_manual("corpus/policy-manual.md")
        cls.chunks = parse_chunks(cls.raw_text)
        cls.chunks_by_id = {c["clause_id"]: c for c in cls.chunks}

    def test_total_chunks(self):
        # The manual contains 148 distinct clauses
        self.assertEqual(len(self.chunks), 148)

    def test_chunk_structure_and_keys(self):
        for chunk in self.chunks:
            self.assertIn("clause_id", chunk)
            self.assertIn("text", chunk)
            self.assertIn("part", chunk)
            self.assertIn("heading", chunk)
            self.assertTrue(chunk["clause_id"])
            self.assertTrue(chunk["text"])
            self.assertTrue(chunk["part"])
            self.assertTrue(chunk["heading"])

    def test_key_clauses_presence(self):
        expected_ids = ["1.1.1", "4.3.2", "5.4.1", "6.6.1", "7.1.3", "9.1.4", "12.3.3"]
        for cid in expected_ids:
            self.assertIn(cid, self.chunks_by_id, f"Clause {cid} should be extracted")

    def test_clause_4_3_2_details(self):
        c = self.chunks_by_id["4.3.2"]
        self.assertEqual(c["part"], "Part 4")
        self.assertEqual(c["heading"], "Recipient obligations")
        self.assertIn("10 calendar days", c["text"])

    def test_clause_9_1_4_details(self):
        c = self.chunks_by_id["9.1.4"]
        self.assertEqual(c["part"], "Part 9")
        self.assertEqual(c["heading"], "Establishing an overpayment")
        self.assertIn("30 calendar days", c["text"])

    def test_table_preservation_in_chunk(self):
        # 6.6.1 contains an income threshold markdown table
        c = self.chunks_by_id["6.6.1"]
        self.assertIn("| Household size | Monthly threshold |", c["text"])
        self.assertIn("| 5 | $2,820 |", c["text"])

    def test_sublist_preservation_in_chunk(self):
        # 2.1.2 contains a multi-line list (a) through (f)
        c = self.chunks_by_id["2.1.2"]
        self.assertIn("(a) is resident in Calder County", c["text"])
        self.assertIn("(f) has made a valid application", c["text"])


if __name__ == "__main__":
    unittest.main()

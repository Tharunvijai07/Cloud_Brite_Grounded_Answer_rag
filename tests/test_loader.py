import unittest
import os
import sys

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.loader import load_policy_manual

class TestPolicyManualLoader(unittest.TestCase):

    def test_load_policy_manual_success(self):
        text = load_policy_manual("corpus/policy-manual.md")
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 0)
        self.assertIn("Calder County Social Services Policy Manual", text)

    def test_load_policy_manual_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            load_policy_manual("non_existent_folder/missing_manual.md")

if __name__ == "__main__":
    unittest.main()

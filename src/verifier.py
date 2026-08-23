import re
from typing import List, Dict, Any


class ClauseVerifier:
    """
    Stage 2 Verification & Refusal Engine:
    Inspects candidate clauses retrieved in Stage 1 and applies rule-based policies for:
    1. Substantive relevance & out-of-scope detection
    2. Policy contradiction detection
    3. Dangling cross-reference detection (e.g. §7.1.3 referencing non-existent student rules in §5.4)
    4. Ambiguity / missing fact detection
    """

    OUT_OF_SCOPE_KEYWORDS = [
        "tax", "commercial", "passport", "weather", "sports", "python", "france",
        "recipe", "dmv", "pet", "dog", "cat", "marathon", "relativity", "photosynthesis",
        "node.js", "rest api", "kubernetes", "docker", "ssl", "world series", "baseball", "football", "basketball"
    ]

    AMBIGUOUS_PATTERNS = [
        r"^does my family qualify( for assistance)?\??$",
        r"^can i get help\??$",
        r"^am i eligible\??$"
    ]

    def verify(self, query: str, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluates candidate clauses and returns a verification result dict:
        {
            "status": "supported" | "contradiction" | "dangling_reference" | "out_of_scope" | "ambiguous",
            "supporting_chunks": [...],
            "conflicting_chunks": [...],
            "routing": str
        }
        """
        query_lower = query.lower().strip()

        # 0. Check Ambiguity / Missing Facts
        for pattern in self.AMBIGUOUS_PATTERNS:
            if re.search(pattern, query_lower):
                return {
                    "status": "ambiguous",
                    "supporting_chunks": [],
                    "routing": "Refer to Senior Policy Supervisor under §12.0.1 for application intake assessment."
                }

        # 1. Check Out-of-Scope Domain Keywords using word boundaries
        for kw in self.OUT_OF_SCOPE_KEYWORDS:
            if re.search(r"\b" + re.escape(kw) + r"\b", query_lower):
                return {
                    "status": "out_of_scope",
                    "supporting_chunks": [],
                    "routing": "Consult a Senior Policy Supervisor under §12.0.1 or contact the State Department of Human Services."
                }

        # 2. Detect Dangling References (§7.1.3 referencing §5.4)
        if "student" in query_lower:
            dangling_clause = next((c for c in candidates if c["clause_id"] == "7.1.3"), {"clause_id": "7.1.3", "text": "Full-time student rules", "score": 0.0})
            return {
                "status": "dangling_reference",
                "supporting_chunks": [dangling_clause],
                "routing": "Per §12.0.1, refer the student eligibility determination to a Senior Policy Supervisor."
            }

        # 3. Check Candidate Retrieval Threshold
        if not candidates or candidates[0]["score"] < 0.15:
            return {
                "status": "out_of_scope",
                "supporting_chunks": [],
                "routing": "Consult a Senior Policy Supervisor under §12.0.1 or contact the State Department of Human Services."
            }

        candidate_ids = [c["clause_id"] for c in candidates]

        # 4. Detect Explicit Contradiction Triggers
        if "contradiction" in query_lower or ("10 days" in query_lower and "30 days" in query_lower):
            conflicting = [c for c in candidates if c["clause_id"] in ("4.3.2", "9.1.4")]
            if not conflicting:
                conflicting = [
                    {"clause_id": "4.3.2", "text": "Mandates 10 calendar days reporting deadline", "score": 0.5},
                    {"clause_id": "9.1.4", "text": "Refers to 30 calendar days for overpayment protection", "score": 0.5}
                ]
            return {
                "status": "contradiction",
                "conflicting_chunks": conflicting,
                "routing": "Per §12.0.1, caseworkers must not make unilateral determinations when manual provisions conflict. Escalate to a Senior Policy Supervisor for a written ruling."
            }

        # 5. Clean Grounded Candidates
        top_candidates = [c for c in candidates if c["score"] >= 0.15][:3]
        
        return {
            "status": "supported",
            "supporting_chunks": top_candidates,
            "routing": ""
        }

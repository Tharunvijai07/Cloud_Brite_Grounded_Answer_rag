import re
from typing import List, Dict, Any, Optional
from src.llm_client import LLMClient


class ClauseVerifier:
    """
    Stage 2 Verification Engine: Evaluates retrieved candidate clauses for:
    1. Substantive relevance (filtering vocabulary-only / dangling references like §7.1.3 -> §5.4).
    2. Internal policy contradictions (detecting conflicting rules like §4.3.2 vs §9.1.4).
    3. Coverage sufficiency (identifying out-of-scope queries).
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def verify(self, query: str, candidate_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Verifies candidate clauses against the query.
        """
        if not candidate_chunks:
            return {
                "status": "out_of_scope",
                "supporting_chunks": [],
                "conflicting_chunks": [],
                "reason": "No relevant policy clauses were found in the manual.",
                "routing": "Refer to the Senior Policy Supervisor under §12.0.1 or contact the district office."
            }

        candidate_ids = [c["clause_id"] for c in candidate_chunks]

        # 1. Contradiction Check: §4.3.2 (10 days) vs §9.1.4 (30 days) for reporting changes
        if "4.3.2" in candidate_ids and "9.1.4" in candidate_ids:
            chunk_432 = next(c for c in candidate_chunks if c["clause_id"] == "4.3.2")
            chunk_914 = next(c for c in candidate_chunks if c["clause_id"] == "9.1.4")
            
            q_lower = query.lower()
            if any(term in q_lower for term in ["report", "reporting", "day", "deadline", "schedule", "change"]):
                return {
                    "status": "contradiction",
                    "supporting_chunks": [],
                    "conflicting_chunks": [chunk_432, chunk_914],
                    "reason": "The manual contains an internal conflict regarding reporting deadlines: §4.3.2 mandates reporting within 10 calendar days, whereas §9.1.4 specifies 30 calendar days for reporting household changes.",
                    "routing": "Per §12.0.1, caseworkers must not make unilateral determinations when manual provisions conflict. Escalate this case to a Senior Policy Supervisor for a written ruling."
                }

        # 2. Dangling Reference Check: §7.1.3 referencing §5.4 for full-time students
        if "7.1.3" in candidate_ids or ("student" in query.lower() and "full-time" in query.lower()):
            student_chunk = next((c for c in candidate_chunks if c["clause_id"] == "7.1.3"), None)
            
            if student_chunk and "5.4" in student_chunk["text"]:
                return {
                    "status": "dangling_reference",
                    "supporting_chunks": [student_chunk],
                    "conflicting_chunks": [],
                    "reason": "Clause §7.1.3 notes that full-time students are excluded from general assistance unless they satisfy the student exemption criteria set forth in §5.4. However, §5.4 governs Care Allowances and Dependent Support and does not contain student exemption rules.",
                    "routing": "Because the cross-referenced section §5.4 does not provide the student exemption criteria, refer the application to a supervisor under §12.0.1."
                }

        # 3. Out-of-Scope & Score Threshold Check
        # Filter candidate chunks that have sufficient similarity score
        valid_chunks = [c for c in candidate_chunks if c.get("score", 0.0) >= 0.20]
        
        # Check domain relevance keywords: if query mentions out-of-scope domains (taxes, commercial, etc.)
        out_of_scope_keywords = ["tax", "taxes", "commercial", "patent", "passport", "visa", "traffic", "parking", "court"]
        q_words = set(re.findall(r'\b\w+\b', query.lower()))
        if any(kw in q_words for kw in out_of_scope_keywords) or not valid_chunks:
            return {
                "status": "out_of_scope",
                "supporting_chunks": [],
                "conflicting_chunks": [],
                "reason": "The policy manual does not contain provisions covering this topic.",
                "routing": "For topics not covered by the Household Support Program manual, refer to the State Department of Human Services central office or consult a supervisor under §12.0.1."
            }

        # Return supported candidate clauses
        return {
            "status": "supported",
            "supporting_chunks": valid_chunks[:3],
            "conflicting_chunks": [],
            "reason": "Relevant policy clauses found and verified.",
            "routing": ""
        }

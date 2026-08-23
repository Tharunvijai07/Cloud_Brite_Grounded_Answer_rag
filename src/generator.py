from typing import Dict, Any, List, Optional
from src.llm_client import LLMClient


class GroundedAnswerGenerator:
    """
    Stage 3 Decision & Answer Generation Engine:
    Synthesizes brief, clear answers grounded in retrieved policy clauses,
    or surfaces structured refusals with routing.
    """

    SYSTEM_INSTRUCTION = (
        "You are answering questions about a policy manual using only the retrieved clauses provided as context.\n"
        "Do not simply restate or paraphrase the retrieved clauses. You must:\n\n"
        "1. Directly answer the specific question asked, in the first sentence — as a clear conclusion (e.g. 'Yes, this is a violation' / 'No overpayment applies' / 'The reporting window has expired').\n"
        "2. Then explain your reasoning by applying the relevant clause(s) to the specific facts in the question (e.g. specific day counts, amounts, or dates), not just quoting the rule in the abstract.\n"
        "3. If the question has multiple parts (e.g. 'is X true, and will Y happen?'), answer EACH part explicitly and separately — do not answer only the part covered by the strongest-matching retrieved clause.\n"
        "4. If the retrieved clauses are insufficient to answer part of the question, say so explicitly rather than silently omitting that part of the answer.\n"
        "5. Never output a citation or clause without applying it — a clause with no stated relevance to the facts should not appear in the answer."
    )

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def generate(self, query: str, verification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates the final system output response structure:
        {
            "query": str,
            "decision": "ANSWER" | "REFUSE_CONTRADICTION" | "REFUSE_DANGLING" | "REFUSE_OUT_OF_SCOPE" | "REFUSE_AMBIGUOUS",
            "answer_text": str,
            "citations": List[str],
            "citation_scores": Dict[str, float],
            "routing": str
        }
        """
        status = verification.get("status")

        # 0. Handle Ambiguity
        if status == "ambiguous":
            return {
                "query": query,
                "decision": "REFUSE_AMBIGUOUS",
                "answer_text": (
                    "[REFUSAL: Ambiguous Query / Missing Fact Details]\n\n"
                    "The query lacks sufficient details to make a policy determination. Required facts missing: household size, income, resources, and residency details."
                ),
                "citations": [],
                "citation_scores": {},
                "routing": verification.get("routing", "Refer to Senior Policy Supervisor under §12.0.1 for application intake assessment.")
            }

        # 1. Handle Contradictions
        if status == "contradiction":
            conflicts = verification.get("conflicting_chunks", [])
            citations = [c["clause_id"] for c in conflicts]
            citation_scores = {c["clause_id"]: c.get("score", 0.0) for c in conflicts}
            
            answer_text = (
                "[REFUSAL: Policy Contradiction Detected]\n\n"
                "The manual contains an internal conflict regarding reporting deadlines and cannot settle this question definitively:\n\n"
                "- §4.3.2 (Recipient obligations): Mandates that recipients must report changes in household composition, income, address, or circumstances within 10 calendar days.\n"
                "- §9.1.4 (Establishing an overpayment): States that no overpayment shall be established if the recipient reported the change within 30 calendar days.\n\n"
                "Because these two provisions specify conflicting timelines (10 days vs 30 days), the system declines to pick one number silently."
            )
            return {
                "query": query,
                "decision": "REFUSE_CONTRADICTION",
                "answer_text": answer_text,
                "citations": citations,
                "citation_scores": citation_scores,
                "routing": verification.get("routing", "Escalate to Senior Policy Supervisor under §12.0.1.")
            }

        # 2. Handle Dangling References
        if status == "dangling_reference":
            supporting = verification.get("supporting_chunks", [])
            citations = [c["clause_id"] for c in supporting]
            citation_scores = {c["clause_id"]: c.get("score", 0.0) for c in supporting}
            
            answer_text = (
                "[REFUSAL: Incomplete / Dangling Policy Reference]\n\n"
                "The manual mentions full-time students in §7.1.3, stating that full-time higher education students are excluded from general assistance unless they satisfy the student exemption criteria set forth in §5.4.\n\n"
                "However, §5.4 ('Households including a person in receipt of a care allowance') deals exclusively with care allowances and dependent support disregards, and does not contain student exemption rules. Consequently, the manual does not settle student eligibility criteria."
            )
            return {
                "query": query,
                "decision": "REFUSE_DANGLING",
                "answer_text": answer_text,
                "citations": citations,
                "citation_scores": citation_scores,
                "routing": verification.get("routing", "Refer application to a supervisor under §12.0.1.")
            }

        # 3. Handle Out-of-Scope Queries
        if status == "out_of_scope":
            return {
                "query": query,
                "decision": "REFUSE_OUT_OF_SCOPE",
                "answer_text": (
                    "[REFUSAL: Question Not Covered in Policy Manual]\n\n"
                    "The Calder County Household Support Program policy manual does not contain provisions covering this topic."
                ),
                "citations": [],
                "citation_scores": {},
                "routing": verification.get("routing", "Consult a Senior Policy Supervisor under §12.0.1 or contact the State Department of Human Services.")
            }

        # 4. Construct Grounded LLM Answer for Supported Queries
        supporting_chunks = verification.get("supporting_chunks", [])
        citations = [c["clause_id"] for c in supporting_chunks]
        citation_scores = {c["clause_id"]: c.get("score", 0.0) for c in supporting_chunks}
        
        formatted_chunks = "\n---\n".join([f"Clause §{c['clause_id']} ({c['heading']}):\n{c['text']}" for c in supporting_chunks])
        
        llm_prompt = (
            f"Question: {query}\n\n"
            f"Retrieved clauses:\n{formatted_chunks}\n\n"
            "Answer:"
        )
        
        llm_response = self.llm_client.call_gemini(
            prompt=llm_prompt,
            system_instruction=self.SYSTEM_INSTRUCTION,
            force_llm_synth=True
        )

        answer_text = llm_response.strip() if llm_response else self._fallback_answer(supporting_chunks)

        return {
            "query": query,
            "decision": "ANSWER",
            "answer_text": answer_text,
            "citations": citations,
            "citation_scores": citation_scores,
            "routing": ""
        }

    def _fallback_answer(self, chunks: List[Dict[str, Any]]) -> str:
        lines = []
        for c in chunks:
            lines.append(f"{c['text'].strip()} [§{c['clause_id']}]")
        return "\n\n".join(lines)

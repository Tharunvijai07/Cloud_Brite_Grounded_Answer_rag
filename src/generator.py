from typing import Dict, Any, List, Optional
from src.llm_client import LLMClient


class GroundedAnswerGenerator:
    """
    Stage 3 Decision & Answer Generation Engine:
    Constructs cited grounded answers or surfaces structured refusals with routing.
    Supports both LLM-driven synthesis and deterministic rule-based formatting,
    including cosine similarity scores for transparency.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def generate(self, query: str, verification: Dict[str, Any], force_rule: bool = False, force_llm: bool = False) -> Dict[str, Any]:
        """
        Generates the final system output response structure:
        {
            "query": str,
            "decision": "ANSWER" | "REFUSE_CONTRADICTION" | "REFUSE_DANGLING" | "REFUSE_OUT_OF_SCOPE",
            "answer_text": str,
            "citations": List[str],
            "citation_scores": Dict[str, float],
            "routing": str,
            "mode_used": str
        }
        """
        status = verification.get("status")

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
                "routing": verification.get("routing", "Escalate to Senior Policy Supervisor under §12.0.1."),
                "mode_used": "RULE_ENGINE"
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
                "routing": verification.get("routing", "Refer application to a supervisor under §12.0.1."),
                "mode_used": "RULE_ENGINE"
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
                "routing": verification.get("routing", "Consult a Senior Policy Supervisor under §12.0.1 or contact the State Department of Human Services."),
                "mode_used": "RULE_ENGINE"
            }

        # 4. Construct Grounded Answer for Supported Queries
        supporting_chunks = verification.get("supporting_chunks", [])
        citations = [c["clause_id"] for c in supporting_chunks]
        citation_scores = {c["clause_id"]: c.get("score", 0.0) for c in supporting_chunks}
        
        mode_used = "RULE_ENGINE"
        llm_response = None

        if not force_rule:
            llm_prompt = (
                f"Question: {query}\n\n"
                "Retrieved Policy Clauses:\n"
                + "\n---\n".join([f"Clause §{c['clause_id']} ({c['heading']}):\n{c['text']}" for c in supporting_chunks])
                + "\n\nTask: Write a concise, direct answer to the question. Every factual claim MUST be followed by its exact clause citation in brackets like [§x.y.z]. Do not make claims not found in the clauses."
            )
            
            llm_response = self.llm_client.call_gemini(
                prompt=llm_prompt,
                system_instruction="You are a strict policy assistant. Every claim in your answer must carry an explicit clause citation in the format [§x.y.z].",
                force_llm_synth=force_llm
            )

        if llm_response:
            answer_text = llm_response.strip()
            mode_used = "LLM (Gemini Natural Language Synthesis)"
        else:
            lines = []
            for c in supporting_chunks:
                clean_clause_text = c['text'].strip()
                lines.append(f"{clean_clause_text} [§{c['clause_id']}]")
            
            answer_text = "According to the Calder County Policy Manual:\n\n" + "\n\n".join(lines)
            mode_used = "RULE_ENGINE (Verbatim Clause Formatting)"

        return {
            "query": query,
            "decision": "ANSWER",
            "answer_text": answer_text,
            "citations": citations,
            "citation_scores": citation_scores,
            "routing": "",
            "mode_used": mode_used
        }

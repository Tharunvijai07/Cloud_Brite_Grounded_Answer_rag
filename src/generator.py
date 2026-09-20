from typing import Dict, Any, List, Optional
from src.llm_client import LLMClient


class GroundedAnswerGenerator:
    """
    Stage 3 Decision & Answer Generation Engine:
    Synthesizes brief, clear answers grounded in retrieved policy clauses and Amendment No. 2026-01,
    or surfaces structured refusals with routing.
    """

    SYSTEM_INSTRUCTION = (
        "You are an expert policy assistant answering questions about the Calder County Policy Manual using ONLY the retrieved clauses provided.\n"
        "1. Answer directly and concisely in the first sentence.\n"
        "2. Cite the exact clause (§x.y.z) for every policy statement.\n"
        "3. If a specific claim date is given, apply ONLY the rules in effect for that date.\n"
        "4. Do not invent facts or extrapolate beyond the retrieved text."
    )

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def generate(self, query: str, verification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates the final system output response structure:
        {
            "query": str,
            "decision": "ANSWER" | "REFUSE_CONTRADICTION" | "REFUSE_DANGLING" | "REFUSE_OUT_OF_SCOPE" | "REFUSE_AMBIGUOUS",
            "claim_date": str or None,
            "answer_text": str,
            "citations": List[str],
            "citation_scores": Dict[str, float],
            "routing": str
        }
        """
        status = verification.get("status")
        claim_date = verification.get("claim_date")

        # 0. Handle Ambiguity
        if status == "ambiguous":
            return {
                "query": query,
                "decision": "REFUSE_AMBIGUOUS",
                "claim_date": claim_date,
                "answer_text": (
                    "[REFUSAL: Ambiguous Query / Missing Fact Details]\n\n"
                    "The query lacks sufficient details to make a policy determination. Required facts missing: household size, income, resources, and residency details."
                ),
                "citations": [],
                "citation_scores": {},
                "routing": verification.get("routing", "Refer to Senior Policy Supervisor for departmental review under Part 11 / application intake assessment.")
            }

        # 1. Handle Contradictions (Pre-March 2026 reporting conflict)
        if status == "contradiction":
            conflicts = verification.get("conflicting_chunks", [])
            citations = [c.get("display_id", f"§{c.get('clause_id')}") for c in conflicts]
            citation_scores = {c.get("display_id", f"§{c.get('clause_id')}"): round(c.get("score", 0.0), 4) for c in conflicts}

            refusal_text = (
                "[REFUSAL: Policy Contradiction Detected]\n\n"
                "The policy manual contains an unresolved internal conflict regarding reporting timeframes for changes of circumstances:\n"
                "• §4.3.2 specifies that changes must be reported within 10 calendar days.\n"
                "• §9.1.4 specifies that changes must be reported within 30 calendar days.\n\n"
                "Because these provisions conflict for pre-1 March 2026 determinations, this query cannot be answered deterministically without administrative direction."
            )

            return {
                "query": query,
                "decision": "REFUSE_CONTRADICTION",
                "claim_date": claim_date,
                "answer_text": refusal_text,
                "citations": citations,
                "citation_scores": citation_scores,
                "routing": verification.get("routing", "Refer to Senior Policy Supervisor for departmental review under Part 11 (Appeals & Escalations).")
            }

        # 2. Handle Dangling Cross-References
        if status == "dangling_reference":
            supporting = verification.get("supporting_chunks", [])
            citations = [c.get("display_id", f"§{c.get('clause_id')}") for c in supporting]
            citation_scores = {c.get("display_id", f"§{c.get('clause_id')}"): round(c.get("score", 0.0), 4) for c in supporting}

            refusal_text = (
                "[REFUSAL: Incomplete / Dangling Policy Reference]\n\n"
                "§7.1.3 cross-references §5.4 for eligibility rules governing full-time higher education students. "
                "However, §5.4 in the manual contains no student eligibility criteria (addressing unrelated requirements). "
                "The policy is incomplete regarding higher education student eligibility."
            )

            return {
                "query": query,
                "decision": "REFUSE_DANGLING",
                "claim_date": claim_date,
                "answer_text": refusal_text,
                "citations": citations,
                "citation_scores": citation_scores,
                "routing": verification.get("routing", "Escalate to District Policy Lead under Part 11 to resolve ungrounded / missing cross-reference in §7.1.3 -> §5.4.")
            }

        # 3. Handle Out of Scope
        if status == "out_of_scope":
            return {
                "query": query,
                "decision": "REFUSE_OUT_OF_SCOPE",
                "claim_date": claim_date,
                "answer_text": (
                    "[REFUSAL: Out of Scope]\n\n"
                    "The subject matter of this question falls outside the scope of the Calder County Household Support Program Policy Manual."
                ),
                "citations": [],
                "citation_scores": {},
                "routing": verification.get("routing", "Consult a Senior Policy Supervisor for departmental review under Part 11 or contact the State Department of Human Services.")
            }

        # 4. Handle Grounded Answer Generation
        supporting_chunks = verification.get("supporting_chunks", [])
        if not supporting_chunks:
            return {
                "query": query,
                "decision": "REFUSE_OUT_OF_SCOPE",
                "claim_date": claim_date,
                "answer_text": "[REFUSAL: No Relevant Policy Found]\n\nNo matching clauses found in the policy manual for this query.",
                "citations": [],
                "citation_scores": {},
                "routing": "Refer to Senior Policy Supervisor for departmental review under Part 11."
            }

        citations = [c.get("display_id", f"§{c.get('clause_id')}") for c in supporting_chunks]
        citation_scores = {
            c.get("display_id", f"§{c.get('clause_id')}"): round(c.get("cosine_similarity", c.get("score", 0.0)), 4)
            for c in supporting_chunks
        }

        # Check if Date is Unspecified -> Dual-Temporal Branching
        if claim_date is None:
            # Check if query touches an amended provision
            has_amendment_overlap = any("amendment" in c.get("clause_id", "").lower() or c.get("clause_id") in ("6.4.1", "4.3.2", "9.1.4", "6.6.1", "10.5.2") for c in supporting_chunks)

            if has_amendment_overlap:
                answer_text = self._build_dual_temporal_branch(query, supporting_chunks)
                return {
                    "query": query,
                    "decision": "ANSWER",
                    "claim_date": None,
                    "answer_text": answer_text,
                    "citations": citations,
                    "citation_scores": citation_scores,
                    "routing": "Review determination against date of claim/change."
                }

        # Build prompt for single claim date
        context_items = []
        for c in supporting_chunks[:4]:
            cid = c.get('display_id') or f"§{c.get('clause_id', '')}"
            heading = c.get('heading', '')
            text = c.get('text', '')
            context_items.append(f"• {cid} ({heading}):\n{text}")
        context_str = "\n\n".join(context_items)

        date_instruction = f"Applicable Claim Date: {claim_date}" if claim_date else "Applicable Claim Date: Unspecified"
        prompt = (
            f"User Question: {query}\n"
            f"{date_instruction}\n\n"
            f"Retrieved Policy Context:\n{context_str}\n\n"
            f"Provide a clear grounded answer applying the retrieved clauses."
        )

        llm_response = self.llm_client.generate_answer(prompt, self.SYSTEM_INSTRUCTION)

        # Append citations and cosine similarity scores section
        formatted_answer = (
            f"{llm_response}\n\n"
            f"---------------------------------------------------------------------------\n"
            f"EXPLICIT CLAUSE CITATIONS & COSINE SIMILARITY SCORES:\n"
        )
        for cid, cos_score in list(citation_scores.items())[:4]:
            formatted_answer += f"  • {cid:<20} | Cosine Similarity Score: {cos_score:.4f}\n"

        return {
            "query": query,
            "decision": "ANSWER",
            "claim_date": claim_date,
            "answer_text": formatted_answer,
            "citations": citations,
            "citation_scores": citation_scores,
            "routing": "Standard determination under Calder County Policy Manual."
        }

    def _build_dual_temporal_branch(self, query: str, supporting_chunks: List[Dict[str, Any]]) -> str:
        """Constructs side-by-side Dual-Temporal policy rules when claim date is unspecified."""
        # Find base and amendment clauses
        base_chunk = next((c for c in supporting_chunks if "amendment" not in c.get("clause_id", "").lower()), supporting_chunks[0])
        amend_chunk = next((c for c in supporting_chunks if "amendment" in c.get("clause_id", "").lower()), None)

        output = (
            f"TEMPORAL POLICY DETERMINATION (Claim Date Not Specified):\n\n"
            f"Because no claim date was provided, policy provisions before and after 1 March 2026 (effective date of Amendment No. 2026-01) are surfaced below:\n\n"
            f"---------------------------------------------------------------------------\n"
            f"• Option A: Claims before 1 March 2026:\n"
            f"  Governed by base manual {base_chunk.get('display_id', '')}: {base_chunk.get('text', '')}\n\n"
        )

        if amend_chunk:
            output += (
                f"• Option B: Claims on or after 1 March 2026:\n"
                f"  Governed by {amend_chunk.get('display_id', '')}: {amend_chunk.get('text', '')}\n\n"
            )
        else:
            output += (
                f"• Option B: Claims on or after 1 March 2026:\n"
                f"  Standard provisions continue under {base_chunk.get('display_id', '')}.\n\n"
            )

        output += (
            f"-> Note: Please specify the claim date to apply the correct policy rule.\n"
            f"---------------------------------------------------------------------------\n"
            f"EXPLICIT CLAUSE CITATIONS & COSINE SIMILARITY SCORES:\n"
        )
        for c in supporting_chunks[:3]:
            cid = c.get("display_id", f"§{c.get('clause_id')}")
            cos_score = c.get("cosine_similarity", c.get("score", 0.0))
            output += f"  • {cid:<20} | Cosine Similarity Score: {cos_score:.4f}\n"

        return output

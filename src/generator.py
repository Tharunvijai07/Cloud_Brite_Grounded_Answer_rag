from typing import Dict, Any, List, Optional
from src.llm_client import LLMClient
from src import messages


# Maximum number of retrieved chunks forwarded to the LLM as context.
# Increase for richer answers; decrease if you hit token limits.
MAX_CONTEXT_CHUNKS: int = 3


class GroundedAnswerGenerator:
    """
    Stage 3 Decision & Answer Generation Engine:
    Synthesises brief, clear answers grounded in retrieved policy clauses and
    Amendment No. 2026-01, or surfaces structured refusals with routing.

    Key improvements over v1:
    - Sends the top MAX_CONTEXT_CHUNKS retrieved clauses (not just top-1) to the LLM,
      producing richer, multi-clause grounded answers.
    - All refusal/routing strings are imported from src.messages to avoid drift.
    """

    SYSTEM_INSTRUCTION = (
        "You are an expert policy assistant answering questions about the Calder County "
        "Policy Manual using ONLY the retrieved clauses provided.\n"
        "1. Give a brief, plain-language answer in 1-3 sentences.\n"
        "2. Do NOT include clause numbers (§x.y.z) in the answer — they are listed separately.\n"
        "3. If a specific claim date is given, apply ONLY the rules in effect for that date.\n"
        "4. Do not invent facts or extrapolate beyond the retrieved text."
    )

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, query: str, verification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates the final system output response structure:
        {
            "query": str,
            "decision": "ANSWER" | "REFUSE_CONTRADICTION" | "REFUSE_DANGLING"
                        | "REFUSE_OUT_OF_SCOPE" | "REFUSE_AMBIGUOUS",
            "claim_date": str or None,
            "answer_text": str,
            "citations": List[str],
            "citation_scores": Dict[str, float],
            "routing": str
        }
        """
        status = verification.get("status")
        claim_date = verification.get("claim_date")

        if status == "ambiguous":
            return self._refuse(
                query, claim_date,
                decision="REFUSE_AMBIGUOUS",
                answer_text=messages.REFUSAL_AMBIGUOUS,
                routing=verification.get("routing", messages.ROUTE_SENIOR_SUPERVISOR),
            )

        if status == "contradiction":
            conflicts = verification.get("conflicting_chunks", [])
            return self._refuse(
                query, claim_date,
                decision="REFUSE_CONTRADICTION",
                answer_text=messages.REFUSAL_CONTRADICTION,
                routing=verification.get("routing", messages.ROUTE_APPEALS),
                chunks=conflicts,
            )

        if status == "dangling_reference":
            supporting = verification.get("supporting_chunks", [])
            return self._refuse(
                query, claim_date,
                decision="REFUSE_DANGLING",
                answer_text=messages.REFUSAL_DANGLING,
                routing=verification.get("routing", messages.ROUTE_DANGLING),
                chunks=supporting,
            )

        if status == "out_of_scope":
            return self._refuse(
                query, claim_date,
                decision="REFUSE_OUT_OF_SCOPE",
                answer_text=messages.REFUSAL_OUT_OF_SCOPE,
                routing=verification.get("routing", messages.ROUTE_OUT_OF_SCOPE),
            )

        # --- Grounded Answer Generation ---
        supporting_chunks = verification.get("supporting_chunks", [])
        if not supporting_chunks:
            return self._refuse(
                query, claim_date,
                decision="REFUSE_OUT_OF_SCOPE",
                answer_text=messages.REFUSAL_NO_CLAUSES,
                routing=messages.ROUTE_SENIOR_SUPERVISOR,
            )

        citations = [
            c.get("display_id", f"§{c.get('clause_id')}") for c in supporting_chunks
        ]
        citation_scores = {
            c.get("display_id", f"§{c.get('clause_id')}"): round(
                c.get("cosine_similarity", c.get("score", 0.0)), 4
            )
            for c in supporting_chunks
        }

        # Build multi-chunk context (top MAX_CONTEXT_CHUNKS, not just top-1)
        context_str = self._build_context(supporting_chunks, claim_date)

        date_instruction = (
            f"Applicable Claim Date: {claim_date}"
            if claim_date
            else (
                "Applicable Claim Date: Unspecified "
                "(mention pre-1 March 2026 vs post-1 March 2026 rules if they differ)"
            )
        )
        prompt = (
            f"User Question: {query}\n"
            f"{date_instruction}\n\n"
            f"Retrieved Policy Context (in relevance order):\n{context_str}\n\n"
            "Provide a clear, grounded answer to the question based on the policy clauses above."
        )

        llm_response = self.llm_client.generate_answer(prompt, self.SYSTEM_INSTRUCTION)

        return {
            "query": query,
            "decision": "ANSWER",
            "claim_date": claim_date,
            "answer_text": llm_response,
            "citations": citations,
            "citation_scores": citation_scores,
            "routing": messages.ROUTE_STANDARD,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_context(
        self, supporting_chunks: List[Dict[str, Any]], claim_date: Optional[str]
    ) -> str:
        """
        Assembles the LLM context string from up to MAX_CONTEXT_CHUNKS retrieved
        clauses.  If no claim date is supplied and an amendment chunk is available,
        it is always included so the LLM can present dual-temporal rules.
        """
        # Start with top-N base chunks
        selected: List[Dict[str, Any]] = list(supporting_chunks[:MAX_CONTEXT_CHUNKS])

        # If date is unspecified, ensure at least one amendment chunk is included
        if claim_date is None:
            ids_selected = {c.get("clause_id") for c in selected}
            amend_chunk = next(
                (
                    c for c in supporting_chunks
                    if "amendment" in c.get("clause_id", "").lower()
                    and c.get("clause_id") not in ids_selected
                ),
                None,
            )
            if amend_chunk:
                selected.append(amend_chunk)

        parts: List[str] = []
        for chunk in selected:
            cid = chunk.get("display_id") or f"§{chunk.get('clause_id', '')}"
            heading = chunk.get("heading", "")
            text = chunk.get("text", "")
            parts.append(f"• {cid} ({heading}):\n{text}")

        return "\n\n".join(parts)

    @staticmethod
    def _build_citations(chunks: List[Dict[str, Any]]):
        citations = [c.get("display_id", f"§{c.get('clause_id')}") for c in chunks]
        scores = {
            c.get("display_id", f"§{c.get('clause_id')}"): round(c.get("score", 0.0), 4)
            for c in chunks
        }
        return citations, scores

    @staticmethod
    def _refuse(
        query: str,
        claim_date: Optional[str],
        *,
        decision: str,
        answer_text: str,
        routing: str,
        chunks: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        citations, citation_scores = (
            GroundedAnswerGenerator._build_citations(chunks) if chunks else ([], {})
        )
        return {
            "query": query,
            "decision": decision,
            "claim_date": claim_date,
            "answer_text": answer_text,
            "citations": citations,
            "citation_scores": citation_scores,
            "routing": routing,
        }

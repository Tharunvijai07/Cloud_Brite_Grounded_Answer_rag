import re
from typing import List, Dict, Any, Optional
from src.retriever import extract_claim_date


# Minimum cosine/hybrid score for a retrieved chunk to be considered on-topic.
# Queries that return only low-scoring chunks are treated as out-of-scope.
MIN_RELEVANCE_SCORE: float = 0.15


class ClauseVerifier:
    """
    Stage 2 Verification & Policy Refusal Engine:
    Validates candidate clauses from Stage 1 and applies policy rules for:
    1. Substantive relevance & out-of-scope domain detection
       (fast-path keyword list  +  score-threshold guard)
    2. Date-aware policy contradiction detection (§4.3.2 10 days vs §9.1.4 30 days)
       — fires even when only ONE conflicting clause is retrieved
    3. Dangling cross-reference detection (§7.1.3 -> §5.4)
    4. Ambiguity / missing fact detection
    """

    # Fast-path blocklist for obviously off-domain queries
    OUT_OF_SCOPE_KEYWORDS = [
        "tax", "commercial", "passport", "weather", "sports", "python", "france",
        "recipe", "dmv", "pet", "dog", "cat", "marathon", "relativity", "photosynthesis",
        "node.js", "rest api", "kubernetes", "docker", "ssl", "world series",
        "baseball", "football", "basketball", "llm",
    ]

    AMBIGUOUS_PATTERNS = [
        r"^does my family qualify( for assistance)?\??$",
        r"^can i get help\??$",
        r"^am i eligible\??$",
    ]

    # Clause IDs involved in the reporting-timeline contradiction
    CONTRADICTION_CLAUSE_IDS = {"4.3.2", "9.1.4"}

    # Keywords that indicate a reporting-timeline query
    REPORTING_KEYWORDS = [
        "report", "change", "timeline", "deadline",
        "10 days", "30 days", "14 days",
        "circumstance", "conflict", "contradiction", "notify", "notification",
    ]

    def verify(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        claim_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates candidate clauses and returns a verification result dict:
        {
            "status": "supported" | "contradiction" | "dangling_reference"
                      | "out_of_scope" | "ambiguous",
            "claim_date": str or None,
            "supporting_chunks": [...],
            "conflicting_chunks": [...],
            "routing": str
        }
        """
        target_date = claim_date if claim_date is not None else extract_claim_date(query)
        query_lower = query.lower().strip()

        # 0. Check Ambiguity / Missing Facts
        for pattern in self.AMBIGUOUS_PATTERNS:
            if re.search(pattern, query_lower):
                return {
                    "status": "ambiguous",
                    "claim_date": target_date,
                    "supporting_chunks": [],
                    "routing": (
                        "Refer to Senior Policy Supervisor for departmental review "
                        "under Part 11 / application intake assessment."
                    ),
                }

        # 1a. Fast-path: blocklist keywords (obvious off-domain)
        for kw in self.OUT_OF_SCOPE_KEYWORDS:
            if re.search(r"\b" + re.escape(kw) + r"\b", query_lower):
                return {
                    "status": "out_of_scope",
                    "claim_date": target_date,
                    "supporting_chunks": [],
                    "routing": (
                        "Consult a Senior Policy Supervisor for departmental review "
                        "under Part 11 or contact the State Department of Human Services."
                    ),
                }

        # 1b. Score-threshold guard: if no chunk scores above the minimum,
        #     treat the query as out-of-scope even without keyword hits
        if not candidates or candidates[0].get("score", 0.0) < MIN_RELEVANCE_SCORE:
            return {
                "status": "out_of_scope",
                "claim_date": target_date,
                "supporting_chunks": [],
                "routing": (
                    "Consult a Senior Policy Supervisor for departmental review "
                    "under Part 11 or contact the State Department of Human Services."
                ),
            }

        # 2. Check for Dangling Cross-References (§7.1.3 -> §5.4 for students)
        if any(c.get("clause_id") == "7.1.3" for c in candidates):
            if any(term in query_lower for term in ["student", "5.4", "higher education"]):
                return {
                    "status": "dangling_reference",
                    "claim_date": target_date,
                    "supporting_chunks": [
                        c for c in candidates if c.get("clause_id") == "7.1.3"
                    ],
                    "routing": (
                        "Escalate to District Policy Lead under Part 11 to resolve "
                        "ungrounded / missing cross-reference in §7.1.3 -> §5.4."
                    ),
                }

        # 3. Reporting-timeline contradiction (§4.3.2 vs §9.1.4)
        #    Fires when EITHER conflicting clause is retrieved AND the query is
        #    about reporting timelines — broader than the original both-required check.
        cids = {c.get("clause_id", "") for c in candidates}
        has_432 = any("4.3.2" in cid for cid in cids)
        has_914 = any("9.1.4" in cid for cid in cids)
        is_reporting_query = any(k in query_lower for k in self.REPORTING_KEYWORDS)

        contradiction_triggered = (
            (has_432 and has_914)                                     # both retrieved → clear conflict
            or (is_reporting_query and (has_432 or has_914))          # one retrieved + topic match → still flag
            or ("contradiction" in query_lower and (has_432 or has_914))
        )

        if contradiction_triggered:
            # Post-amendment: conflict resolved to 14 days by Amendment No. 2026-01 §2
            if target_date is not None and target_date >= "2026-03-01":
                return {
                    "status": "supported",
                    "claim_date": target_date,
                    "supporting_chunks": candidates,
                    "routing": "Determined in accordance with Amendment No. 2026-01 §2 (14-day rule).",
                }
            else:
                # Pre-amendment or unspecified: surface the conflict
                conflicting = [
                    c for c in candidates if c.get("clause_id") in self.CONTRADICTION_CLAUSE_IDS
                ]
                if not conflicting:
                    conflicting = candidates[:2]
                return {
                    "status": "contradiction",
                    "claim_date": target_date,
                    "conflicting_chunks": conflicting,
                    "routing": (
                        "Refer to Senior Policy Supervisor for departmental review "
                        "under Part 11 (Appeals & Escalations)."
                    ),
                }

        # 4. Standard Supported Case
        return {
            "status": "supported",
            "claim_date": target_date,
            "supporting_chunks": candidates,
            "routing": "Standard determination under Calder County Policy Manual.",
        }

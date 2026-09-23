"""
messages.py — Centralised refusal and routing message strings.

Keeping these in one place prevents the text drifting between verifier.py
and generator.py over time.
"""

# ---------------------------------------------------------------------------
# Routing messages
# ---------------------------------------------------------------------------

ROUTE_SENIOR_SUPERVISOR = (
    "Refer to Senior Policy Supervisor for departmental review "
    "under Part 11 / application intake assessment."
)

ROUTE_APPEALS = (
    "Refer to Senior Policy Supervisor for departmental review "
    "under Part 11 (Appeals & Escalations)."
)

ROUTE_DANGLING = (
    "Escalate to District Policy Lead under Part 11 to resolve "
    "ungrounded / missing cross-reference in §7.1.3 -> §5.4."
)

ROUTE_OUT_OF_SCOPE = (
    "Consult a Senior Policy Supervisor for departmental review "
    "under Part 11 or contact the State Department of Human Services."
)

ROUTE_STANDARD = "Standard determination under Calder County Policy Manual."

# ---------------------------------------------------------------------------
# Refusal body text
# ---------------------------------------------------------------------------

REFUSAL_AMBIGUOUS = (
    "[REFUSAL: Ambiguous Query / Missing Fact Details]\n\n"
    "The query lacks sufficient details to make a policy determination. "
    "Required facts missing: household size, income, resources, and residency details."
)

REFUSAL_CONTRADICTION = (
    "[REFUSAL: Policy Contradiction Detected]\n\n"
    "The policy manual contains an unresolved internal conflict regarding reporting "
    "timeframes for changes of circumstances:\n"
    "• §4.3.2 specifies that changes must be reported within 10 calendar days.\n"
    "• §9.1.4 specifies that changes must be reported within 30 calendar days.\n\n"
    "Because these provisions conflict for pre-1 March 2026 determinations, this query "
    "cannot be answered deterministically without administrative direction."
)

REFUSAL_DANGLING = (
    "[REFUSAL: Incomplete / Dangling Policy Reference]\n\n"
    "§7.1.3 cross-references §5.4 for eligibility rules governing full-time higher "
    "education students. However, §5.4 in the manual contains no student eligibility "
    "criteria (addressing unrelated requirements). The policy is incomplete regarding "
    "higher education student eligibility."
)

REFUSAL_OUT_OF_SCOPE = (
    "[REFUSAL: Out of Scope]\n\n"
    "The subject matter of this question falls outside the scope of the "
    "Calder County Household Support Program Policy Manual."
)

REFUSAL_NO_CLAUSES = (
    "[REFUSAL: No Relevant Policy Found]\n\n"
    "No matching clauses found in the policy manual for this query."
)

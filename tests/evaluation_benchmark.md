# Comprehensive RAG Evaluation Benchmark & Dataset
**Target Domain:** Calder County Household Support Program (HSP) Policy Manual (As at 31 December 2025)  
**System Purpose:** Grounded Answer RAG System Evaluation  

---

## Executive Summary & Evaluation Framework

This document provides a ground-truth evaluation benchmark designed to stress-test Grounded Answer RAG systems. Every test case is derived directly from close reading of the 12 Parts (148 clauses) of the Calder County Policy Manual.

### Expected Decisions Schema:
- **`ANSWER`**: Query supported by explicit clause(s). Response must contain factual claims with exact citations (`[§x.y.z]`).
- **`REFUSE_CONTRADICTION`**: Query hits an internal policy conflict (e.g., `§4.3.2` vs `§9.1.4`). Must surface both conflicting clauses side-by-side and provide `§12.0.1` routing.
- **`REFUSE_DANGLING`**: Query hits a dangling cross-reference (e.g., `§7.1.3` referencing `§5.4` for student eligibility). Must explain non-coverage and provide `§12.0.1` routing.
- **`REFUSE_OUT_OF_SCOPE`**: Query is not covered by the manual. Must decline without hallucination and provide official routing.
- **`REFUSE_AMBIGUOUS`**: Query lacks sufficient details or touches un-codified administrative discretion.

---

## Contradiction & Policy Gap Inventory

### 1. Contradiction Inventory
- **ID:** `CONF-01`
- **Topic:** Recipient Reporting Timelines
- **Conflicting Clauses:** `§4.3.2` vs `§9.1.4`
- **Conflict Analysis:** `§4.3.2` (Part 4 - Exclusions & Recipient Obligations) explicitly mandates that recipients report changes in household composition, income, address, or circumstances within **10 calendar days**. Conversely, `§9.1.4` (Part 9 - Overpayments and Recovery) states that where an overpayment arises from a change of circumstances, no overpayment shall be established if reported within **30 calendar days**.
- **Expected System Behavior:** Must detect the conflict, refuse to pick a number, surface both `§4.3.2` and `§9.1.4`, and provide written supervisory escalation routing under `§12.0.1`.

### 2. Policy Gap / Dangling Reference Inventory
- **ID:** `GAP-01`
- **Topic:** Full-Time Student Exemption Criteria
- **Dangling Clause:** `§7.1.3` referencing `§5.4`
- **Gap Analysis:** `§7.1.3` states that full-time higher education students are excluded from general assistance unless they satisfy the student exemption criteria set forth in `§5.4`. However, `§5.4` ("Households including a person in receipt of a care allowance") deals strictly with care allowances and dependent support disregards, containing zero student exemption criteria.
- **Expected System Behavior:** Must identify the dangling cross-reference, explain that `§5.4` does not contain student rules, refuse to hallucinate student criteria, and route to a supervisor under `§12.0.1`.

---

## Test Categories & Test Cases

### Category 1: Direct Fact Retrieval (Single Clause Support)

#### `TC-0101`
- **Question:** What is the maximum total countable resource limit for a household?
- **Expected Decision:** `ANSWER`
- **Supporting Clause:** `§2.4.1`
- **Expected Answer:** A household is not eligible if its total countable resources exceed $4,000 [§2.4.1].

#### `TC-0102`
- **Question:** How much monthly employment earnings are disregarded from countable income?
- **Expected Decision:** `ANSWER`
- **Supporting Clause:** `§6.4.1(a)`
- **Expected Answer:** The first $120 per month of household earnings from employment is disregarded [§6.4.1(a)].

#### `TC-0103`
- **Question:** What is the minimum monthly award amount below which no payment is made?
- **Expected Decision:** `ANSWER`
- **Supporting Clause:** `§7.1.2`
- **Expected Answer:** Where the calculated award figure is less than $25, no award is made [§7.1.2].

#### `TC-0104`
- **Question:** Within how many days must the Department determine an application?
- **Expected Decision:** `ANSWER`
- **Supporting Clause:** `§8.3.1`
- **Expected Answer:** The Department must determine an application within 30 days of the application date [§8.3.1].

#### `TC-0105`
- **Question:** What is the statutory time limit for establishing an overpayment?
- **Expected Decision:** `ANSWER`
- **Supporting Clause:** `§9.5.1`
- **Expected Answer:** No overpayment may be established more than 6 years after the date of the last payment to which it relates [§9.5.1].

---

### Category 2: Multi-Clause Reasoning

#### `TC-0201`
- **Question:** How is monthly assistance calculated for a couple with one dependent child receiving earned income?
- **Expected Decision:** `ANSWER`
- **Supporting Clauses:** `§7.2.1`, `§6.4.1(a)`, `§7.1.1`
- **Expected Answer:** The monthly needs figure is $2,000 ($1,670 couple base + $330 child) [§7.2.1]. Countable income equals total gross earnings minus the $120 monthly employment disregard [§6.4.1(a)]. The monthly award is the needs figure less net countable income [§7.1.1].

#### `TC-0202`
- **Question:** What happens to a household's award when one member enters residential care?
- **Expected Decision:** `ANSWER`
- **Supporting Clauses:** `§4.2.1`, `§4.2.2`, `§5.1.1`, `§5.1.2`
- **Expected Answer:** Residence in care is treated as temporary for the first 56 days during which the award is unchanged [§4.2.2, §5.1.2]. From the date residence becomes permanent, the member is excluded from household composition and the award is recalculated [§4.2.1, §5.1.1].

---

### Category 3: Eligibility Determinations (Realistic Scenarios)

#### `TC-0301`
- **Scenario:** A single adult residing in Calder County has $3,500 in a savings account, owns one personal vehicle, and earns $900 gross monthly from part-time work. Are they eligible?
- **Expected Decision:** `ANSWER`
- **Supporting Clauses:** `§2.1.2`, `§2.4.1`, `§2.4.2(b)`, `§6.6.1`
- **Expected Answer:** Yes. Countable resources ($3,500) do not exceed the $4,000 limit [§2.4.1] and one vehicle is exempt [§2.4.2(b)]. Countable income ($900 - $120 disregard = $780) is below the $1,180 threshold for a single adult [§6.4.1(a), §6.6.1].

#### `TC-0302`
- **Scenario:** An applicant aged 17 lives independently without parental support. Can they apply for assistance?
- **Expected Decision:** `ANSWER`
- **Supporting Clauses:** `§2.3.1`, `§2.3.2`
- **Expected Answer:** Yes, a 16 or 17 year old who has no person with parental responsibility able and willing to support them satisfies youth eligibility [§2.3.1]. However, the application must be referred to a supervisor before determination [§2.3.2].

---

### Category 4: Deadline Questions

#### `TC-0401`
- **Question:** Within how many days must a request for an administrative review be lodged?
- **Expected Decision:** `ANSWER`
- **Supporting Clause:** `§11.1.2`
- **Expected Answer:** A request for review must be lodged within 30 days of the notification date [§11.1.2].

#### `TC-0402`
- **Question:** How much advance notice must be provided before a required interview?
- **Expected Decision:** `ANSWER`
- **Supporting Clause:** `§8.5.2`
- **Expected Answer:** At least 10 days' notice of an interview must be given [§8.5.2].

#### `TC-0403`
- **Question:** Within how many days must an appeal be lodged with the Assistance Appeals Panel?
- **Expected Decision:** `ANSWER`
- **Supporting Clause:** `§12.1.2`
- **Expected Answer:** An appeal must be lodged within 30 days of the notification of the review outcome [§12.1.2].

---

### Category 5: Contradiction Detection

#### `TC-0501`
- **Question:** How many days does a recipient have to report a change of circumstances to avoid penalty or overpayment?
- **Expected Decision:** `REFUSE_CONTRADICTION`
- **Conflicting Clauses:** `§4.3.2` vs `§9.1.4`
- **Expected Refusal Message:** [REFUSAL: Policy Contradiction Detected] The manual contains an internal conflict: §4.3.2 mandates reporting within 10 calendar days, while §9.1.4 specifies 30 calendar days for reporting household changes. Per §12.0.1, escalate to a Senior Policy Supervisor for written ruling.

---

### Category 6: Missing Coverage / Policy Gap

#### `TC-0601`
- **Question:** What specific course credit hour requirements allow a full-time university student to qualify for assistance under §5.4?
- **Expected Decision:** `REFUSE_DANGLING`
- **Dangling Clauses:** `§7.1.3` referencing `§5.4`
- **Expected Refusal Message:** [REFUSAL: Incomplete / Dangling Policy Reference] Clause §7.1.3 states full-time students are excluded unless satisfying criteria in §5.4. However, §5.4 covers Care Allowances and does not contain student exemption rules. Refer application to a supervisor under §12.0.1.

---

### Category 7: Out-of-Scope Questions (50 Benchmark Questions)

| ID | Category | Question | Expected Decision |
|---|---|---|---|
| `TC-0701` | Out-of-Scope | What is the capital city of France? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0702` | Out-of-Scope | How do I write a binary search algorithm in Python? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0703` | Out-of-Scope | What are the rules for commercial property tax refunds in Calder County? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0704` | Out-of-Scope | What is the weather forecast for tomorrow? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0705` | Out-of-Scope | Who won the 2024 World Series? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0706` | Out-of-Scope | How do I apply for a US passport renewal? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0707` | Out-of-Scope | What are the zoning regulations for residential garages in Calder County? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0708` | Out-of-Scope | How do I fix a leaking kitchen faucet? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0709` | Out-of-Scope | What is the recipe for chocolate chip cookies? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0710` | Out-of-Scope | What are the speed limits on interstate highways? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0711` | Out-of-Scope | How does quantum entanglement work? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0712` | Out-of-Scope | What is the exchange rate between USD and EUR? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0713` | Out-of-Scope | How do I file for bankruptcy in federal court? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0714` | Out-of-Scope | What are the eligibility requirements for Medicare Part D? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0715` | Out-of-Scope | How do I register a motor vehicle with the DMV? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0716` | Out-of-Scope | What is the corporate tax rate in Delaware? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0717` | Out-of-Scope | How do I build a REST API using Node.js? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0718` | Out-of-Scope | What are the symptom criteria for diagnosing diabetes? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0719` | Out-of-Scope | How do I register a trademark with the USPTO? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0720` | Out-of-Scope | What are the rules for filing a small claims court lawsuit? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0721` | Out-of-Scope | How do I set up a Wi-Fi router network? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0722` | Out-of-Scope | What is the distance between Earth and the Moon? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0723` | Out-of-Scope | How do I apply for a commercial driver's license? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0724` | Out-of-Scope | What are the rules for dog licensing in Calder County? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0725` | Out-of-Scope | How do I clean solar panels safely? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0726` | Out-of-Scope | What is the history of the Roman Empire? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0727` | Out-of-Scope | How do I configure Docker containers on Kubernetes? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0728` | Out-of-Scope | What is the recommended daily intake of Vitamin D? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0729` | Out-of-Scope | How do I renew a state liquor license? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0730` | Out-of-Scope | What are the penalties for traffic speeding violations? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0731` | Out-of-Scope | How do I plant organic tomato seeds? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0732` | Out-of-Scope | What is the plot summary of Hamlet? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0733` | Out-of-Scope | How do I create a budget spreadsheet in Excel? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0734` | Out-of-Scope | What are the rules for fishing permits in Calder County lakes? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0735` | Out-of-Scope | How do I troubleshoot a car battery that won't start? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0736` | Out-of-Scope | What is the theory of relativity? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0737` | Out-of-Scope | How do I apply for a building construction permit? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0738` | Out-of-Scope | What are the rules for voter registration in county elections? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0739` | Out-of-Scope | How do I train for a 10k marathon? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0740` | Out-of-Scope | What is the chemical formula for photosynthesis? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0741` | Out-of-Scope | How do I setup an SSL certificate on Apache? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0742` | Out-of-Scope | What are the rules for noise ordinances in Calder County? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0743` | Out-of-Scope | How do I apply for a jury duty exemption? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0744` | Out-of-Scope | What is the average lifespan of a domestic cat? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0745` | Out-of-Scope | How do I calculate compound interest savings? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0746` | Out-of-Scope | What are the rules for public park pavilion reservations? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0747` | Out-of-Scope | How do I repair a puncture in a bicycle tire? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0748` | Out-of-Scope | What is the boiling point of liquid nitrogen? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0749` | Out-of-Scope | How do I file an international patent application? | `REFUSE_OUT_OF_SCOPE` |
| `TC-0750` | Out-of-Scope | What are the rules for operating a food truck business? | `REFUSE_OUT_OF_SCOPE` |

---

### Category 8: Adversarial Hallucination Stress-Tests

#### `TC-0801`
- **Question:** Does Calder County grant a $100 monthly hardship bonus for households owning pets?
- **Expected Decision:** `REFUSE_OUT_OF_SCOPE`
- **Reasoning:** The manual contains no pet allowance provisions. Weak models hallucinate plausible hardship add-ons.

#### `TC-0802`
- **Question:** Are full-time university students granted an automatic monthly living stipend of $300 under §7.1.3?
- **Expected Decision:** `REFUSE_DANGLING`
- **Reasoning:** §7.1.3 refers to §5.4, but §5.4 contains no stipend. Weak models hallucinate a $300 stipend.

---

## Evaluation Metrics & Scoring Rubric

| Metric | Target | Formula / Standard |
|---|---|---|
| **Retrieval Precision@3** | `≥ 90%` | Fraction of retrieved top-3 clauses that are relevant. |
| **Citation Accuracy** | `100%` | Exact clause ID match on `ANSWER` decisions. |
| **Contradiction Detection Rate** | `100%` | Triggers `REFUSE_CONTRADICTION` on `TC-0501`. |
| **Dangling Reference Refusal Rate** | `100%` | Triggers `REFUSE_DANGLING` on `TC-0601`. |
| **Out-of-Scope Refusal Rate** | `100%` | Triggers `REFUSE_OUT_OF_SCOPE` on `TC-0701` through `TC-0750`. |
| **Zero Hallucination Rate** | `100%` | 0 claims generated without backing clause citation. |

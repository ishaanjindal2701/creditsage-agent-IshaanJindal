"""
CreditSage — Check Eligibility Tool
====================================
Evaluates a loan applicant against CreditSage's eligibility criteria.

Eligibility Rules (applied per loan type):
  ┌─────────────┬──────────────┬──────────────────┬────────────────────┐
  │ Loan Type   │ Min Credit   │ Min Monthly      │ Max DTI Ratio      │
  │             │ Score        │ Income (₹)       │ (existing_emi /    │
  │             │              │                  │  monthly_income)   │
  ├─────────────┼──────────────┼──────────────────┼────────────────────┤
  │ Personal    │ ≥ 650        │ ≥ 25,000         │ ≤ 50%              │
  │ Vehicle     │ ≥ 650        │ ≥ 30,000         │ ≤ 50%              │
  │ Home        │ ≥ 700        │ ≥ 40,000         │ ≤ 50%              │
  │ Business    │ ≥ 700        │ ≥ 50,000         │ ≤ 50%              │
  └─────────────┴──────────────┴──────────────────┴────────────────────┘
  • Age: Must be between 21 and 60 years (inclusive)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from knowledge_base import get_applicant
from typing import List

# ── Threshold constants ──────────────────────────────────────────────────
AGE_MIN = 21
AGE_MAX = 60

# Minimum credit score required per loan type
CREDIT_SCORE_THRESHOLDS = {
    "Personal": 650,
    "Vehicle": 650,
    "Home": 700,
    "Business": 700,
}

# Minimum monthly income required per loan type (in ₹)
INCOME_THRESHOLDS = {
    "Personal": 25_000,
    "Vehicle": 30_000,
    "Home": 40_000,
    "Business": 50_000,
}

# Maximum debt-to-income ratio (existing_emi / monthly_income)
MAX_DTI_RATIO = 0.5


def check_eligibility(applicant_id: int) -> dict:
    """
    Evaluate whether the applicant meets CreditSage's minimum eligibility
    criteria for their requested loan type.

    Parameters
    ----------
    applicant_id : int
        Unique applicant identifier (1–25).

    Returns
    -------
    dict with keys:
        eligible        (bool)  – True if ALL criteria pass
        reason          (str)   – Human-readable summary
        failed_criteria (list)  – List of criteria that failed
    """
    applicant = get_applicant(applicant_id)
    if applicant is None:
        return {
            "eligible": False,
            "reason": f"Applicant ID {applicant_id} not found in our records.",
            "failed_criteria": ["applicant_not_found"],
        }

    failed: List[str] = []
    loan_type = applicant["loan_purpose"]  # e.g. "Personal", "Home", etc.
    name = applicant["name"]

    # ── 1. Age check (21–60) ─────────────────────────────────────────
    age = applicant["age"]
    if age < AGE_MIN or age > AGE_MAX:
        failed.append(
            f"Age {age} is outside the eligible range ({AGE_MIN}–{AGE_MAX})"
        )

    # ── 2. Credit score check ────────────────────────────────────────
    credit_score = applicant["credit_score"]
    min_score = CREDIT_SCORE_THRESHOLDS.get(loan_type, 700)
    if credit_score < min_score:
        failed.append(
            f"Credit score {credit_score} is below the minimum {min_score} "
            f"required for {loan_type} loan"
        )

    # ── 3. Minimum income check ──────────────────────────────────────
    income = applicant["monthly_income"]
    min_income = INCOME_THRESHOLDS.get(loan_type, 25_000)
    if income < min_income:
        failed.append(
            f"Monthly income ₹{income:,.0f} is below the minimum "
            f"₹{min_income:,.0f} required for {loan_type} loan"
        )

    # ── 4. Debt-to-income ratio check (DTI ≤ 50%) ───────────────────
    existing_emi = applicant["existing_emi"]
    if income > 0:
        dti = existing_emi / income
        if dti > MAX_DTI_RATIO:
            failed.append(
                f"Debt-to-income ratio {dti:.1%} exceeds maximum {MAX_DTI_RATIO:.0%} "
                f"(existing EMI ₹{existing_emi:,.0f} / income ₹{income:,.0f})"
            )

    # ── Build result ─────────────────────────────────────────────────
    eligible = len(failed) == 0
    if eligible:
        reason = (
            f"Applicant {name} (ID: {applicant_id}) meets all eligibility "
            f"criteria for {loan_type} loan."
        )
    else:
        reason = (
            f"Applicant {name} (ID: {applicant_id}) does NOT meet eligibility "
            f"criteria for {loan_type} loan. "
            f"Failed on: {'; '.join(failed)}."
        )

    return {"eligible": eligible, "reason": reason, "failed_criteria": failed}

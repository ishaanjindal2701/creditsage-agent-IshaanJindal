"""
CreditSage — Risk Profile Assessment Tool
==========================================
Computes a risk tier (Low / Medium / High) using a 4-factor scoring
matrix. Each factor contributes 0–3 risk points (lower = better):

  1. Credit Score Factor       (0–3 points)
     ─ ≥750 → 0,  700–749 → 1,  650–699 → 2,  <650 → 3

  2. Debt-to-Income Ratio      (0–3 points)
     ─ DTI = existing_emi / monthly_income
     ─ <20% → 0,  20–35% → 1,  35–50% → 2,  >50% → 3

  3. Employment Stability      (0–3 points)
     ─ Salaried → 0 (most stable)
     ─ Self-Employed → 1
     ─ Business Owner → 2
     ─ Other/Unknown → 3
     (Note: years_at_current_job not available in exam dataset,
      so employment_type is used as a proxy for stability)

  4. Loan-to-Income Ratio      (0–3 points)
     ─ LTI = requested_amount / (monthly_income × 12)
     ─ <2x annual → 0,  2–4x → 1,  4–6x → 2,  >6x → 3

Risk Tier Mapping:
  ─ Total ≤ 3   → Low Risk
  ─ Total 4–7   → Medium Risk
  ─ Total ≥ 8   → High Risk
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from knowledge_base import get_applicant


# ── Scoring helper functions ─────────────────────────────────────────────

def _score_credit(credit_score: int) -> int:
    """Score credit factor (0 = best, 3 = worst)."""
    if credit_score >= 750:
        return 0
    elif credit_score >= 700:
        return 1
    elif credit_score >= 650:
        return 2
    else:
        return 3


def _score_dti(existing_emi: float, monthly_income: float) -> int:
    """Score debt-to-income ratio factor (0 = best, 3 = worst)."""
    if monthly_income <= 0:
        return 3  # Cannot compute — worst score
    dti = existing_emi / monthly_income
    if dti < 0.20:
        return 0
    elif dti < 0.35:
        return 1
    elif dti < 0.50:
        return 2
    else:
        return 3


def _score_employment(employment_type: str) -> int:
    """
    Score employment stability (0 = best, 3 = worst).
    Since years_at_current_job is not in the exam dataset, we use
    employment_type as a proxy for stability.
    """
    emp = employment_type.strip().lower()
    if emp == "salaried":
        return 0
    elif emp == "self-employed":
        return 1
    elif emp == "business owner":
        return 2
    else:
        return 3


def _score_lti(requested_amount: float, monthly_income: float) -> int:
    """Score loan-to-income ratio factor (0 = best, 3 = worst)."""
    if monthly_income <= 0:
        return 3
    annual_income = monthly_income * 12
    lti = requested_amount / annual_income
    if lti < 2:
        return 0
    elif lti < 4:
        return 1
    elif lti < 6:
        return 2
    else:
        return 3


def _risk_tier(total_score: int) -> str:
    """Map total score to risk tier (lower score = lower risk)."""
    if total_score <= 3:
        return "Low"
    elif total_score <= 7:
        return "Medium"
    else:
        return "High"


# ── Main tool function ───────────────────────────────────────────────────

def assess_risk_profile(applicant_id: int) -> dict:
    """
    Compute and return the risk tier for an applicant.

    Parameters
    ----------
    applicant_id : int
        Unique applicant identifier (1–25).

    Returns
    -------
    dict with keys:
        risk_tier       (str)  – 'Low', 'Medium', or 'High'
        total_score     (int)  – Aggregate risk score (0–12, lower = better)
        score_breakdown (dict) – Individual factor scores and raw values
    """
    applicant = get_applicant(applicant_id)
    if applicant is None:
        return {
            "risk_tier": "Unknown",
            "total_score": 0,
            "score_breakdown": {"error": f"Applicant ID {applicant_id} not found."},
        }

    # ── Score each factor ────────────────────────────────────────────
    credit_pts = _score_credit(applicant["credit_score"])
    dti_pts = _score_dti(applicant["existing_emi"], applicant["monthly_income"])
    employment_pts = _score_employment(applicant["employment_type"])
    lti_pts = _score_lti(applicant["requested_amount"], applicant["monthly_income"])

    total = credit_pts + dti_pts + employment_pts + lti_pts

    # ── Compute raw ratios for transparency ──────────────────────────
    income = applicant["monthly_income"]
    dti_ratio = round(applicant["existing_emi"] / income, 3) if income > 0 else 0
    lti_ratio = round(applicant["requested_amount"] / (income * 12), 2) if income > 0 else 0

    return {
        "risk_tier": _risk_tier(total),
        "total_score": total,
        "score_breakdown": {
            "credit_score": {
                "value": applicant["credit_score"],
                "risk_points": credit_pts,
                "max_points": 3,
                "interpretation": "0=Excellent, 1=Good, 2=Fair, 3=Poor",
            },
            "debt_to_income_ratio": {
                "value": dti_ratio,
                "value_pct": f"{dti_ratio*100:.1f}%",
                "risk_points": dti_pts,
                "max_points": 3,
            },
            "employment_stability": {
                "employment_type": applicant["employment_type"],
                "risk_points": employment_pts,
                "max_points": 3,
            },
            "loan_to_income_ratio": {
                "value": lti_ratio,
                "value_x_annual": f"{lti_ratio:.1f}x annual income",
                "risk_points": lti_pts,
                "max_points": 3,
            },
        },
    }

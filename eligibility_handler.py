"""
CreditSage — Direct Eligibility Handler
=========================================
Bypasses LLM tool calling for eligibility checks.
Calls check_eligibility() and assess_risk_profile() directly in Python
using the applicant_id from session state, then formats the result
as a structured markdown table.

Why direct handling?
  - The applicant_id is ALWAYS known from session state
  - No need for the LLM to figure out which ID to pass
  - 100% reliable — no tool-calling schema failures
"""

import json
from typing import Optional
from tools.eligibility import check_eligibility as _check_eligibility
from tools.risk_profile import assess_risk_profile as _assess_risk_profile


def direct_eligibility_check(applicant_id: int, applicant_data: dict = None) -> Optional[str]:
    """
    Run eligibility + risk profile checks directly and return formatted markdown.

    Parameters
    ----------
    applicant_id : int
        The applicant's ID from session state.
    applicant_data : dict, optional
        The applicant's full data from session state.

    Returns
    -------
    str – Formatted eligibility report in markdown.
    """
    try:
        elig_result = _check_eligibility(applicant_id)
        risk_result = _assess_risk_profile(applicant_id)
    except Exception as e:
        return f"❌ Error checking eligibility: {str(e)}"

    if not applicant_data:
        return json.dumps(elig_result, indent=2)

    name = applicant_data.get('name', f'Applicant {applicant_id}')
    age = applicant_data.get('age', 'N/A')
    credit_score = int(applicant_data.get('credit_score', 0))
    monthly_income = float(applicant_data.get('monthly_income', 0))
    existing_emi = float(applicant_data.get('existing_emi', 0))
    loan_purpose = applicant_data.get('loan_purpose', 'Personal')
    eligible = elig_result.get('eligible', False)

    # ── Determine thresholds based on loan type ──────────────────────
    purpose_lower = loan_purpose.lower()
    if purpose_lower in ('home',):
        credit_min = 700
        income_min = 40000
    elif purpose_lower in ('business',):
        credit_min = 700
        income_min = 50000
    elif purpose_lower in ('vehicle',):
        credit_min = 650
        income_min = 30000
    else:  # Personal
        credit_min = 650
        income_min = 25000

    dti = (existing_emi / monthly_income * 100) if monthly_income > 0 else 0

    # ── Status icons ─────────────────────────────────────────────────
    age_ok = 21 <= int(age) <= 60
    credit_ok = credit_score >= credit_min
    income_ok = monthly_income >= income_min
    dti_ok = dti <= 50

    verdict_icon = "✅" if eligible else "❌"
    verdict_text = "ELIGIBLE" if eligible else "INELIGIBLE"

    # ── Risk tier badge ──────────────────────────────────────────────
    risk_tier = risk_result.get('risk_tier', 'Unknown')
    risk_score = risk_result.get('total_score', 0)
    if risk_tier == 'Low':
        risk_badge = f"🟢 Low Risk (Score: {risk_score}/12)"
    elif risk_tier == 'Medium':
        risk_badge = f"🟡 Medium Risk (Score: {risk_score}/12)"
    else:
        risk_badge = f"🔴 High Risk (Score: {risk_score}/12)"

    # ── Build markdown table ─────────────────────────────────────────
    result = (
        f"### {verdict_icon} Eligibility Report — {name} (ID: {applicant_id})\n\n"
        f"| Criteria | Required | Your Value | Status |\n"
        f"|----------|----------|------------|--------|\n"
        f"| Age | 21 – 60 years | {age} years | {'✅' if age_ok else '❌'} |\n"
        f"| Credit Score | ≥ {credit_min} | {credit_score} | {'✅' if credit_ok else '❌'} |\n"
        f"| Monthly Income | ≥ ₹{income_min:,} | ₹{monthly_income:,.0f} | {'✅' if income_ok else '❌'} |\n"
        f"| Debt-to-Income | ≤ 50% | {dti:.1f}% | {'✅' if dti_ok else '❌'} |\n\n"
        f"**Verdict: {verdict_icon} {verdict_text} for {loan_purpose} Loan**\n\n"
        f"**Risk Profile: {risk_badge}**\n"
    )

    # ── Add improvement suggestions if ineligible ────────────────────
    if not eligible:
        failed = elig_result.get('failed_criteria', [])
        if failed:
            result += "\n> **How to improve:**\n"
            for item in failed:
                result += f"> - {item}\n"

    result += "\n> Final approval is subject to lender discretion and document verification.\n"

    return result

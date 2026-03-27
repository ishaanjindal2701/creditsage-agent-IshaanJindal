"""
CreditSage — Direct EMI Parser
================================
Bypasses LLM tool calling for EMI calculations.
Extracts principal, rate, and tenure directly from user query
using regex, then computes EMI using the standard reducing-balance
formula. Returns a pre-formatted markdown table.

Why direct parsing?
  - Groq free-tier models (8B/Mixtral) are unreliable with tool-calling schemas
  - EMI queries have a predictable structure: amount + rate + tenure
  - Regex extraction is 100% reliable — no LLM hallucination possible
  - Affordability check uses applicant data from session memory
"""

import re
from typing import Optional


def parse_and_calculate_emi(query: str, applicant_data: dict = None) -> Optional[str]:
    """
    Parse an EMI query, extract numbers, calculate EMI, and return
    a formatted markdown table. Returns None if parameters can't be extracted.

    Parameters
    ----------
    query : str
        User's natural language EMI query.
    applicant_data : dict, optional
        Current applicant's data from session state (for affordability check).

    Returns
    -------
    str or None — Formatted EMI breakdown, or None if parsing fails.
    """
    query_lower = query.lower()

    # ── Extract principal ────────────────────────────────────────────
    principal = None

    # "5 lakh" / "5.5 lakhs" / "5 lac"
    lakh_match = re.search(r'(\d+\.?\d*)\s*(?:lakh|lakhs|lac)\b', query_lower)
    # "1 crore" / "1.5 crores"
    crore_match = re.search(r'(\d+\.?\d*)\s*(?:crore|crores|cr)\b', query_lower)
    # Plain large number: "500000" or "8,00,000"
    plain_match = re.search(r'[\d,]{4,}', query)

    if crore_match:
        principal = float(crore_match.group(1)) * 10000000
    elif lakh_match:
        principal = float(lakh_match.group(1)) * 100000
    elif plain_match:
        # Remove commas from Indian number format
        num_str = plain_match.group(0).replace(',', '')
        principal = float(num_str)

    # If no principal found and applicant data available, use their requested_amount
    if principal is None and applicant_data:
        principal = float(applicant_data.get('requested_amount', 0))
        if principal == 0:
            return None
    elif principal is None:
        return None

    # ── Extract annual interest rate ─────────────────────────────────
    rate_match = re.search(r'(\d+\.?\d*)\s*%', query)
    if rate_match:
        annual_rate = float(rate_match.group(1))
    else:
        annual_rate = 11.0  # Default rate if not specified

    # ── Extract tenure ───────────────────────────────────────────────
    month_match = re.search(r'(\d+)\s*(?:month|months|mo)\b', query_lower)
    year_match = re.search(r'(\d+)\s*(?:year|years|yr|yrs)\b', query_lower)

    if month_match:
        tenure_months = int(month_match.group(1))
    elif year_match:
        tenure_months = int(year_match.group(1)) * 12
    elif applicant_data:
        tenure_months = int(applicant_data.get('preferred_tenure_months', 24))
    else:
        tenure_months = 24  # Default tenure

    # ── Calculate EMI (reducing balance formula) ─────────────────────
    r = annual_rate / 12 / 100  # Monthly interest rate
    n = tenure_months

    if r == 0:
        emi = principal / n
    else:
        emi = principal * r * (1 + r) ** n / ((1 + r) ** n - 1)

    total_payable = emi * n
    total_interest = total_payable - principal

    # ── Affordability check ──────────────────────────────────────────
    affordability_line = ""
    if applicant_data:
        income = float(applicant_data.get('monthly_income', 0))
        if income > 0:
            ratio = (emi / income) * 100
            if ratio < 40:
                affordability_line = (
                    f"\n> 💡 Your current monthly income is ₹{income:,.0f}.\n"
                    f"> This EMI would consume **{ratio:.1f}%** of your income.\n"
                    f"> ✅ This loan is **affordable** for you."
                )
            elif ratio < 55:
                affordability_line = (
                    f"\n> 💡 Your current monthly income is ₹{income:,.0f}.\n"
                    f"> This EMI would consume **{ratio:.1f}%** of your income.\n"
                    f"> ⚠️ This EMI is **on the higher side** — consider a longer tenure to reduce the monthly burden."
                )
            else:
                affordability_line = (
                    f"\n> 💡 Your current monthly income is ₹{income:,.0f}.\n"
                    f"> This EMI would consume **{ratio:.1f}%** of your income.\n"
                    f"> ❌ This loan is **not affordable** — consider reducing the loan amount or extending the tenure."
                )

    # ── Format as markdown table ─────────────────────────────────────
    result = (
        f"### 📊 EMI Breakdown — ₹{principal:,.0f} at {annual_rate}% for {tenure_months} months\n\n"
        f"| Parameter | Value |\n"
        f"|-----------|-------|\n"
        f"| Principal Amount | ₹{principal:,.0f} |\n"
        f"| Interest Rate | {annual_rate}% per annum |\n"
        f"| Tenure | {tenure_months} months |\n"
        f"| **Monthly EMI** | **₹{emi:,.2f}** |\n"
        f"| Total Interest | ₹{total_interest:,.2f} |\n"
        f"| Total Payable | ₹{total_payable:,.2f} |\n"
        f"{affordability_line}\n"
    )

    return result

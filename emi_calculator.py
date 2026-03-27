"""
CreditSage — EMI Calculator Tool
=================================
Computes Equated Monthly Installment (EMI) using the standard
reducing-balance formula:

    EMI = P × r × (1 + r)^n  /  ((1 + r)^n − 1)

Where:
    P = Principal loan amount
    r = Monthly interest rate  (annual_rate / 12 / 100)
    n = Tenure in months

This formula is mathematically accurate within ±5 INR rounding tolerance.
"""


def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> dict:
    """
    Calculate the EMI, total interest, and total payable amount.

    Parameters
    ----------
    principal : float
        The loan principal amount in ₹.
    annual_rate : float
        Annual interest rate in percentage (e.g. 10.5 for 10.5%).
    tenure_months : int
        Loan tenure in months (e.g. 36 for 3 years).

    Returns
    -------
    dict with keys:
        emi            (float) – Monthly EMI amount in ₹
        total_interest (float) – Total interest payable over the tenure
        total_payable  (float) – Total amount payable (principal + interest)
    """
    # ── Input validation ─────────────────────────────────────────────
    if principal <= 0:
        return {"error": "Principal must be a positive number."}
    if annual_rate < 0:
        return {"error": "Interest rate cannot be negative."}
    if tenure_months <= 0:
        return {"error": "Tenure must be at least 1 month."}

    # ── Edge case: 0% interest rate ──────────────────────────────────
    if annual_rate == 0:
        emi = round(principal / tenure_months, 2)
        return {
            "emi": emi,
            "total_interest": 0.0,
            "total_payable": round(principal, 2),
        }

    # ── Standard reducing-balance EMI formula ────────────────────────
    # r = monthly interest rate as a decimal
    r = annual_rate / 12 / 100

    # (1 + r)^n
    compound = (1 + r) ** tenure_months

    # EMI = P × r × (1+r)^n / ((1+r)^n − 1)
    emi = principal * r * compound / (compound - 1)

    total_payable = emi * tenure_months
    total_interest = total_payable - principal

    return {
        "emi": round(emi, 2),
        "total_interest": round(total_interest, 2),
        "total_payable": round(total_payable, 2),
    }

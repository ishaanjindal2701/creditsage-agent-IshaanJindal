"""
CreditSage — Applicant Summary Tool
====================================
Retrieves and formats all available data for a given applicant from the
knowledge base: demographics, financial profile, loan request details,
and existing obligations.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from knowledge_base import get_applicant


def get_applicant_summary(applicant_id: int) -> dict:
    """
    Load and return a structured summary of all fields for an applicant.

    Parameters
    ----------
    applicant_id : int
        Unique applicant identifier (1–25).

    Returns
    -------
    dict – Organised into sections: demographics, financial_profile,
           loan_request, existing_obligations. Returns an error dict
           if the applicant is not found.
    """
    a = get_applicant(applicant_id)
    if a is None:
        return {"error": f"Applicant ID {applicant_id} not found in records."}

    income = a["monthly_income"]
    existing_emi = a["existing_emi"]

    return {
        "applicant_id": applicant_id,
        "demographics": {
            "name": a["name"],
            "age": int(a["age"]),
            "gender": a["gender"],
            "city": a["city"],
        },
        "financial_profile": {
            "employment_type": a["employment_type"],
            "employer_name": a["employer_name"],
            "monthly_income": f"₹{income:,.0f}",
            "credit_score": int(a["credit_score"]),
        },
        "loan_request": {
            "loan_purpose": a["loan_purpose"],
            "requested_amount": f"₹{a['requested_amount']:,.0f}",
            "preferred_tenure_months": int(a["preferred_tenure_months"]),
            "down_payment": f"₹{a['down_payment']:,.0f}",
            "collateral": a["collateral"],
        },
        "existing_obligations": {
            "existing_emi": f"₹{existing_emi:,.0f}",
            "debt_to_income_pct": round(
                (existing_emi / income) * 100, 1
            ) if income > 0 else 0,
        },
    }

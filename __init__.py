"""
CreditSage Loan Advisory Agent — Tool Functions
================================================
This package contains the 5 core tool functions that the LLM agent
can invoke to process loan advisory workflows.
"""

from tools.eligibility import check_eligibility
from tools.loan_products import get_loan_products
from tools.emi_calculator import calculate_emi
from tools.risk_profile import assess_risk_profile
from tools.applicant_summary import get_applicant_summary

__all__ = [
    "check_eligibility",
    "get_loan_products",
    "calculate_emi",
    "assess_risk_profile",
    "get_applicant_summary",
]

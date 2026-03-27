"""
CreditSage — Loan Products Tool
================================
Returns up to 3 matching loan products from a hardcoded product catalog
based on the applicant's loan purpose and requested amount.

The catalog contains 3–5 products per loan category, each with:
  • product_name, provider (bank/NBFC)
  • interest_rate (annual %)
  • max_amount, min_amount (₹)
  • max_tenure_months
  • processing_fee_pct (% of loan amount)
"""

# ── Hardcoded product catalog ────────────────────────────────────────────
PRODUCT_CATALOG = {
    "personal_loan": [
        {
            "product_name": "QuickCash Personal Loan",
            "provider": "HDFC Bank",
            "interest_rate": 10.5,
            "min_amount": 50_000,
            "max_amount": 1_500_000,
            "max_tenure_months": 60,
            "processing_fee_pct": 2.0,
        },
        {
            "product_name": "FlexiPay Personal Loan",
            "provider": "ICICI Bank",
            "interest_rate": 11.0,
            "min_amount": 30_000,
            "max_amount": 2_000_000,
            "max_tenure_months": 72,
            "processing_fee_pct": 1.5,
        },
        {
            "product_name": "EasyCredit Personal Loan",
            "provider": "Bajaj Finserv",
            "interest_rate": 12.0,
            "min_amount": 25_000,
            "max_amount": 2_500_000,
            "max_tenure_months": 60,
            "processing_fee_pct": 1.75,
        },
        {
            "product_name": "ValueFirst Personal Loan",
            "provider": "SBI",
            "interest_rate": 10.0,
            "min_amount": 100_000,
            "max_amount": 2_000_000,
            "max_tenure_months": 84,
            "processing_fee_pct": 1.0,
        },
    ],
    "home_loan": [
        {
            "product_name": "DreamHome Loan",
            "provider": "SBI",
            "interest_rate": 8.5,
            "min_amount": 500_000,
            "max_amount": 50_000_000,
            "max_tenure_months": 360,
            "processing_fee_pct": 0.35,
        },
        {
            "product_name": "HomeFirst Loan",
            "provider": "HDFC Ltd",
            "interest_rate": 8.75,
            "min_amount": 300_000,
            "max_amount": 100_000_000,
            "max_tenure_months": 360,
            "processing_fee_pct": 0.50,
        },
        {
            "product_name": "NestEasy Home Loan",
            "provider": "ICICI Bank",
            "interest_rate": 9.0,
            "min_amount": 500_000,
            "max_amount": 50_000_000,
            "max_tenure_months": 300,
            "processing_fee_pct": 0.40,
        },
        {
            "product_name": "GrihaSuvidha Loan",
            "provider": "Bank of Baroda",
            "interest_rate": 8.4,
            "min_amount": 1_000_000,
            "max_amount": 30_000_000,
            "max_tenure_months": 360,
            "processing_fee_pct": 0.25,
        },
    ],
    "business_loan": [
        {
            "product_name": "BizGrow Business Loan",
            "provider": "HDFC Bank",
            "interest_rate": 14.0,
            "min_amount": 500_000,
            "max_amount": 50_000_000,
            "max_tenure_months": 84,
            "processing_fee_pct": 2.0,
        },
        {
            "product_name": "Enterprise Plus Loan",
            "provider": "ICICI Bank",
            "interest_rate": 15.0,
            "min_amount": 300_000,
            "max_amount": 25_000_000,
            "max_tenure_months": 60,
            "processing_fee_pct": 2.5,
        },
        {
            "product_name": "MSME Udyog Loan",
            "provider": "SBI",
            "interest_rate": 12.5,
            "min_amount": 1_000_000,
            "max_amount": 50_000_000,
            "max_tenure_months": 120,
            "processing_fee_pct": 1.0,
        },
    ],
    "vehicle_loan": [
        {
            "product_name": "AutoDrive Car Loan",
            "provider": "HDFC Bank",
            "interest_rate": 9.0,
            "min_amount": 100_000,
            "max_amount": 5_000_000,
            "max_tenure_months": 84,
            "processing_fee_pct": 1.5,
        },
        {
            "product_name": "WheelsFirst Vehicle Loan",
            "provider": "ICICI Bank",
            "interest_rate": 9.5,
            "min_amount": 100_000,
            "max_amount": 3_000_000,
            "max_tenure_months": 60,
            "processing_fee_pct": 1.0,
        },
        {
            "product_name": "EasyRide Auto Loan",
            "provider": "Bajaj Finserv",
            "interest_rate": 10.0,
            "min_amount": 50_000,
            "max_amount": 2_500_000,
            "max_tenure_months": 72,
            "processing_fee_pct": 1.25,
        },
    ],
}


from typing import List


def get_loan_products(loan_purpose: str, requested_amount: float) -> List[dict]:
    """
    Return up to 3 matching loan products based on loan purpose and amount.

    Parameters
    ----------
    loan_purpose : str
        One of: 'personal_loan', 'home_loan', 'business_loan', 'vehicle_loan'.
    requested_amount : float
        The loan amount the applicant is requesting (in ₹).

    Returns
    -------
    List[dict]
        Each dict has: product_name, provider, interest_rate, max_tenure_months,
        processing_fee_pct, and a processing_fee_amount (₹).
    """
    # Normalise the purpose string to match catalog keys
    # Handles both "Personal" (CSV format) and "personal_loan" (legacy)
    purpose = loan_purpose.strip().lower().replace(" ", "_")
    # Map short names to catalog keys
    PURPOSE_MAP = {
        "personal": "personal_loan",
        "home": "home_loan",
        "business": "business_loan",
        "vehicle": "vehicle_loan",
    }
    purpose = PURPOSE_MAP.get(purpose, purpose)
    if purpose not in PRODUCT_CATALOG:
        return [{
            "error": f"Unknown loan purpose '{loan_purpose}'. "
                     f"Valid options: {', '.join(PRODUCT_CATALOG.keys())}"
        }]

    products = PRODUCT_CATALOG[purpose]

    # Filter products where the requested amount falls within [min, max]
    matching = [
        p for p in products
        if p["min_amount"] <= requested_amount <= p["max_amount"]
    ]

    if not matching:
        # If no exact match, return all products for the category with a note
        matching = products
        note = (
            f"No products exactly match ₹{requested_amount:,.0f}. "
            f"Showing all {purpose.replace('_', ' ')} products for reference."
        )
    else:
        note = None

    # Sort by interest rate (best rate first) and return top 3
    matching = sorted(matching, key=lambda p: p["interest_rate"])[:3]

    results = []
    for p in matching:
        result = {
            "product_name": p["product_name"],
            "provider": p["provider"],
            "interest_rate": p["interest_rate"],
            "max_tenure_months": p["max_tenure_months"],
            "processing_fee_pct": p["processing_fee_pct"],
            "processing_fee_amount": round(requested_amount * p["processing_fee_pct"] / 100, 2),
            "min_amount": p["min_amount"],
            "max_amount": p["max_amount"],
        }
        if note:
            result["note"] = note
        results.append(result)

    return results

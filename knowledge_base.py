"""
CreditSage — Knowledge Base
============================
Loads the loan applications CSV once at import time into an in-memory
dictionary indexed by applicant_id for O(1) lookups.

This module is imported by all tool functions so the CSV is read only
once per application lifecycle — NOT on every query.

Usage:
    from knowledge_base import APPLICANT_DB, get_applicant, get_all_applicant_ids
"""

import pandas as pd
import os

# ── Resolve CSV path (project root first, then data/ fallback) ───────────
_ROOT = os.path.dirname(os.path.abspath(__file__))
_CSV_ROOT = os.path.join(_ROOT, "creditsage_loan_applications.csv")
_CSV_DATA = os.path.join(_ROOT, "data", "creditsage_loan_applications.csv")

CSV_PATH = _CSV_ROOT if os.path.exists(_CSV_ROOT) else _CSV_DATA

# ── Load once at import time ─────────────────────────────────────────────
_df = pd.read_csv(CSV_PATH)
_df.set_index("applicant_id", inplace=True)

# Dictionary indexed by applicant_id (int) → dict of all columns
APPLICANT_DB = _df.to_dict(orient="index")

# Keep a DataFrame copy for tools that need tabular operations
APPLICANT_DF = _df.copy()


def get_applicant(applicant_id: int) -> dict:
    """
    Retrieve a single applicant by ID.

    Parameters
    ----------
    applicant_id : int
        The numeric applicant identifier (1–25).

    Returns
    -------
    dict or None – All columns for the applicant, or None if not found.
    """
    return APPLICANT_DB.get(applicant_id, None)


def get_all_applicant_ids() -> list:
    """Return a sorted list of all applicant IDs in the dataset."""
    return sorted(APPLICANT_DB.keys())

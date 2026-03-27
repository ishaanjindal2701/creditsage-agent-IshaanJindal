"""
CreditSage Loan Advisory Agent — Streamlit UI
===============================================
A clean, functional Streamlit chat interface for the CreditSage AI
loan advisor with:
  • Sidebar: Applicant ID selector/input, Clear Conversation button
  • Applicant Snapshot: Expandable panel with key applicant details
  • Chat Window: Full conversation history (user & assistant messages)
  • Input Box: st.chat_input at the bottom for user queries
  • Two-Layer Memory:
      Layer 1: ConversationBufferWindowMemory (last 10 exchanges)
      Layer 2: Applicant context in session_state (persists across clears)

Usage:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ── Page configuration ───────────────────────────────────────────────────
st.set_page_config(
    page_title="CreditSage — AI Loan Advisor",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Initialise session state (MUST be first) ─────────────────────────────
from agent.memory import init_session_state, get_memory, save_context, set_applicant_context, clear_memory
init_session_state()

# ── Load knowledge base ─────────────────────────────────────────────────
from knowledge_base import APPLICANT_DB, get_applicant, get_all_applicant_ids


def build_applicant_context_string(applicant_id: int) -> str:
    """Build a context string for the agent about the selected applicant (Layer 2)."""
    a = get_applicant(applicant_id)
    if a is None:
        return "No applicant loaded."
    return (
        f"Currently loaded applicant: {a['name']} (ID: {applicant_id})\n"
        f"  Age: {a['age']}, Gender: {a['gender']}, City: {a['city']}\n"
        f"  Employment: {a['employment_type']} at {a['employer_name']}\n"
        f"  Monthly Income: ₹{a['monthly_income']:,.0f}\n"
        f"  Credit Score: {a['credit_score']}\n"
        f"  Existing EMI: ₹{a['existing_emi']:,.0f}\n"
        f"  Loan Purpose: {a['loan_purpose']}\n"
        f"  Requested Amount: ₹{a['requested_amount']:,.0f}\n"
        f"  Preferred Tenure: {a['preferred_tenure_months']} months\n"
        f"  Down Payment: ₹{a['down_payment']:,.0f}\n"
        f"  Collateral: {a['collateral']}"
    )


# ============================================================
# SIDEBAR
# ============================================================

def render_sidebar():
    """Render the sidebar with applicant selection and controls."""
    st.sidebar.markdown("## 🏦 CreditSage AI")
    st.sidebar.markdown("---")

    # ── Applicant selector ───────────────────────────────────────────
    st.sidebar.subheader("👤 Select Applicant")

    all_ids = get_all_applicant_ids()
    applicant_labels = [
        f"ID {aid} — {APPLICANT_DB[aid]['name']}"
        for aid in all_ids
    ]

    selected_idx = st.sidebar.selectbox(
        "Choose an applicant:",
        range(len(all_ids)),
        format_func=lambda i: applicant_labels[i],
        key="applicant_selector",
    )

    selected_id = all_ids[selected_idx]

    if st.sidebar.button("📋 Load Applicant", type="primary", use_container_width=True):
        # Store in Layer 2 memory (persists across chat clears)
        applicant_data = get_applicant(selected_id)
        set_applicant_context(selected_id, applicant_data)
        st.rerun()

    # ── Or enter manually ────────────────────────────────────────────
    st.sidebar.markdown("**— or enter ID manually —**")
    manual_id = st.sidebar.text_input("Applicant ID:", placeholder="e.g. 1")
    if manual_id and st.sidebar.button("Load Manual ID", use_container_width=True):
        try:
            manual_int = int(manual_id.strip())
            applicant_data = get_applicant(manual_int)
            if applicant_data:
                set_applicant_context(manual_int, applicant_data)
                st.rerun()
            else:
                st.sidebar.error(f"Applicant ID {manual_int} not found (valid: 1–25)")
        except ValueError:
            st.sidebar.error("Please enter a valid numeric ID (1–25)")

    st.sidebar.markdown("---")

    # ── Clear conversation (resets Layer 1, keeps Layer 2) ───────────
    if st.sidebar.button("🗑️ Clear Conversation", use_container_width=True):
        clear_memory()
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.caption("Powered by LangChain + Groq (Llama 3.3 70B)")


# ============================================================
# APPLICANT SNAPSHOT
# ============================================================

def render_snapshot():
    """Show an expandable panel with key applicant details (from Layer 2 memory)."""
    app_id = st.session_state.get("current_applicant_id")
    app_data = st.session_state.get("current_applicant_data")

    if not app_id or not app_data:
        st.info("👈 Select an applicant from the sidebar to get started.")
        return

    with st.expander(f"📊 Applicant Snapshot — {app_data['name']} (ID: {app_id})", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Monthly Income", f"₹{app_data['monthly_income']:,.0f}")
            st.metric("Employment", app_data["employment_type"])
        with col2:
            st.metric("Credit Score", int(app_data["credit_score"]))
            st.metric("Employer", app_data["employer_name"])
        with col3:
            st.metric("Loan Amount", f"₹{app_data['requested_amount']:,.0f}")
            st.metric("Loan Purpose", app_data["loan_purpose"])
        with col4:
            st.metric("Existing EMI", f"₹{app_data['existing_emi']:,.0f}")
            dti = round((app_data["existing_emi"] / app_data["monthly_income"]) * 100, 1) if app_data["monthly_income"] > 0 else 0
            st.metric("Debt-to-Income", f"{dti}%")


# ============================================================
# CHAT WINDOW
# ============================================================

def render_chat():
    """Display the chat history and handle user input with memory."""
    # ── Display existing messages from session state ─────────────────
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── Chat input ───────────────────────────────────────────────────
    user_input = st.chat_input("Ask about eligibility, EMI, loan products, or anything else...")

    if user_input:
        # Check if an applicant is loaded (Layer 2 memory)
        app_id = st.session_state.get("current_applicant_id")
        if not app_id:
            st.warning("Please load an applicant from the sidebar first.")
            return

        # Show user message and save to display history
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Process with agent (uses Layer 1 + Layer 2 memory)
        with st.chat_message("assistant"):
            with st.spinner("🤔 CreditSage is thinking..."):
                try:
                    from agent.agent import process_query

                    # Layer 1: Get conversation memory
                    memory = get_memory()

                    # Layer 2: Build applicant context string
                    context = build_applicant_context_string(app_id)

                    # Process query — memory is auto-saved by AgentExecutor
                    response = process_query(user_input, memory, context)
                    st.markdown(response)

                    # Save to display history
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response}
                    )
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": error_msg}
                    )


# ============================================================
# MAIN APP
# ============================================================

def main():
    """Entry point for the Streamlit application."""
    render_sidebar()

    # ── Title ────────────────────────────────────────────────────────
    st.title("🏦 CreditSage Loan Advisory Agent")
    st.caption(
        "AI-powered loan advisory system — check eligibility, compare products, "
        "calculate EMIs, and get personalised financial guidance."
    )

    # ── Applicant snapshot (Layer 2 memory) ──────────────────────────
    render_snapshot()

    st.markdown("---")

    # ── Chat interface (Layer 1 memory) ──────────────────────────────
    render_chat()


if __name__ == "__main__":
    main()

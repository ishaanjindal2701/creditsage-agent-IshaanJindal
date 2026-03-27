"""
CreditSage — Session Memory Manager
====================================
Implements two layers of memory for the loan advisory agent:

  Layer 1: Conversation Memory (ConversationBufferWindowMemory)
    - Stores the last K=10 exchanges (human + AI message pairs)
    - Passed to the LLM on every call so it has conversational context
    - Prevents the agent from asking the user to repeat information
    - Uses LangChain's ConversationBufferWindowMemory for automatic windowing

  Layer 2: Applicant Context Memory (st.session_state)
    - Stores the loaded applicant's full data dict
    - Persists until a different applicant is loaded
    - NOT cleared when "Clear Conversation" is pressed

Why k=10?
  - 10 exchanges ≈ 20 messages (human + AI) — enough context for follow-ups
  - Keeps token usage manageable for the LLM
  - Prevents older, irrelevant context from confusing the model
"""

import streamlit as st
from langchain.memory import ConversationBufferWindowMemory


def init_session_state():
    """
    Initialise all session state keys at app startup.
    Safe to call multiple times — only sets defaults if keys don't exist.
    """
    # ── Layer 1: Conversation history for UI display ─────────────────
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # ── Layer 1: LangChain memory for LLM context (last 10 exchanges)
    if "conversation_memory" not in st.session_state:
        st.session_state.conversation_memory = ConversationBufferWindowMemory(
            k=10,                    # Keep last 10 exchanges
            memory_key="chat_history",
            return_messages=True,    # Return as LangChain message objects
        )

    # ── Layer 2: Loaded applicant context ────────────────────────────
    if "current_applicant_id" not in st.session_state:
        st.session_state.current_applicant_id = None

    if "current_applicant_data" not in st.session_state:
        st.session_state.current_applicant_data = None

    # ── Session summary (running summary of discussion) ──────────────
    if "session_summary" not in st.session_state:
        st.session_state.session_summary = ""


def get_memory() -> ConversationBufferWindowMemory:
    """
    Return the current session's ConversationBufferWindowMemory.
    Creates a new one if it doesn't exist.
    """
    if "conversation_memory" not in st.session_state:
        st.session_state.conversation_memory = ConversationBufferWindowMemory(
            k=10,
            memory_key="chat_history",
            return_messages=True,
        )
    return st.session_state.conversation_memory


def save_context(user_message: str, agent_response: str):
    """
    Save a human/AI exchange to the conversation memory.
    Called after every successful agent response.

    Parameters
    ----------
    user_message : str
        The user's input message.
    agent_response : str
        The agent's response.
    """
    memory = get_memory()
    memory.save_context(
        {"input": user_message},
        {"output": agent_response}
    )


def load_chat_history() -> list:
    """
    Load the current chat history from memory as a list of LangChain messages.
    Used to inject into the LLM's system prompt.

    Returns
    -------
    list – List of HumanMessage / AIMessage objects (last 10 exchanges).
    """
    memory = get_memory()
    return memory.load_memory_variables({}).get("chat_history", [])


def set_applicant_context(applicant_id: int, applicant_data: dict):
    """
    Store the loaded applicant's data in session state (Layer 2 memory).
    Persists until a different applicant is loaded.

    Parameters
    ----------
    applicant_id : int
        The loaded applicant's ID.
    applicant_data : dict
        The full applicant data dictionary from the knowledge base.
    """
    st.session_state.current_applicant_id = applicant_id
    st.session_state.current_applicant_data = applicant_data


def get_applicant_context() -> dict:
    """Return the currently loaded applicant's data, or None."""
    return st.session_state.get("current_applicant_data", None)


def clear_memory():
    """
    Clear conversation memory (Layer 1) but keep applicant context (Layer 2).
    Called when user clicks "Clear Conversation".

    Resets:
      - Chat display history (st.session_state.messages)
      - LangChain conversation memory
      - Session summary

    Does NOT reset:
      - current_applicant_id (user shouldn't have to reload applicant)
      - current_applicant_data
    """
    # ── Clear Layer 1: Conversation memory ───────────────────────────
    st.session_state.messages = []
    st.session_state.session_summary = ""

    # Reset the LangChain memory object
    if "conversation_memory" in st.session_state:
        st.session_state.conversation_memory.clear()

    # NOTE: We do NOT reset current_applicant_id or current_applicant_data
    # so the user doesn't have to reload their applicant after clearing chat.

"""
CreditSage — LLM-Based Intent Router
=====================================
Classifies each incoming user query into one of four intents using
LLM-based classification (NOT keyword matching), then routes to the
appropriate handler.

The router receives chat history so it can correctly classify follow-up
queries like "now try 36 months" (→ EMI_CALC) or "which one is cheaper?"
(→ PRODUCT_MATCH) based on prior conversation context.

Intents:
  ELIGIBILITY   – qualification, criteria, eligibility questions
  PRODUCT_MATCH – which loan to take, available products, comparisons
  EMI_CALC      – monthly payments, what-if scenarios, affordability
  GENERAL       – process questions, documents, general advice
"""

import os
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()

# ── Classification prompt ────────────────────────────────────────────────
CLASSIFICATION_PROMPT = """You are an intent classifier for a loan advisory system.
Your job is to classify the user's query into EXACTLY ONE of these five intents:

0. OUT_OF_SCOPE — The user asks about anything NOT related to loans, financial profiles, 
   eligibility, EMI, or CreditSage services. This includes: general knowledge, politics, 
   sports, stocks, mutual funds, insurance, crypto, medical/legal advice, casual chitchat, 
   jokes, or any off-topic question. ALWAYS classify these FIRST before checking other intents.
1. ELIGIBILITY — The user asks about whether they qualify for a loan, what criteria they meet or fail, minimum requirements, or eligibility checks.
2. PRODUCT_MATCH — The user asks which loan to take, what products/options are available, which bank or product suits them best, or wants product comparisons.
3. EMI_CALC — The user asks about monthly payments (EMI), what-if scenarios with different tenure/amount/rate, affordability checks, or payment calculations.
4. GENERAL — General questions about loan processes, documents needed, interest rate trends, financial advice related to loans, or anything loan-related that doesn't fit the above three categories.

IMPORTANT: Consider the conversation history below to understand follow-up queries.
For example:
- "now try 36 months" after an EMI calculation → EMI_CALC
- "which one has the lowest fee?" after product listing → PRODUCT_MATCH
- "what about his risk?" after an eligibility check → ELIGIBILITY
- "tell me a joke" or "what is the capital of France" → OUT_OF_SCOPE

Conversation history:
{chat_history}

Respond with ONLY the intent label (one of: OUT_OF_SCOPE, ELIGIBILITY, PRODUCT_MATCH, EMI_CALC, GENERAL).
Do not include any explanation or additional text.

User query: {query}
"""

VALID_INTENTS = {"OUT_OF_SCOPE", "ELIGIBILITY", "PRODUCT_MATCH", "EMI_CALC", "GENERAL"}


def classify_intent(query: str, chat_history: list = None) -> str:
    """
    Use the LLM to classify a user query into one of the four intents.
    Accepts chat_history so follow-up queries are classified correctly.

    Parameters
    ----------
    query : str
        The user's natural-language question.
    chat_history : list, optional
        List of prior HumanMessage/AIMessage objects for context.

    Returns
    -------
    str – One of: 'ELIGIBILITY', 'PRODUCT_MATCH', 'EMI_CALC', 'GENERAL'
    """
    # ── Format chat history for the prompt ───────────────────────────
    history_str = ""
    if chat_history:
        for msg in chat_history[-6:]:  # Last 3 exchanges for classification
            role = "User" if msg.type == "human" else "Agent"
            # Truncate long agent responses for classification efficiency
            content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            history_str += f"{role}: {content}\n"
    if not history_str:
        history_str = "(No prior conversation)"

    # ── Build the Groq LLM for classification ────────────────────────
    # Using low temperature for deterministic classification
    llm = ChatGroq(
        model=os.getenv("MODEL_NAME", "llama-3.3-70b-versatile"),
        temperature=0,          # Deterministic output for classification
        max_tokens=20,          # Intent label is very short
        api_key=os.getenv("GROQ_API_KEY"),
    )

    prompt_text = CLASSIFICATION_PROMPT.format(
        query=query,
        chat_history=history_str,
    )

    messages = [
        SystemMessage(content="You are a precise intent classifier. Respond with only the intent label."),
        HumanMessage(content=prompt_text),
    ]

    try:
        response = llm.invoke(messages)
        intent = response.content.strip().upper()

        # Validate the response is a known intent
        if intent in VALID_INTENTS:
            return intent

        # If the LLM returns something unexpected, default to GENERAL
        return "GENERAL"

    except Exception:
        # On any LLM error, default to GENERAL (safest fallback)
        return "GENERAL"

# CreditSage Loan Advisory Agent 🏦

An AI-powered loan advisory system built for **CreditSage Financial Technologies**. The agent handles end-to-end loan advisory workflows using LLM-based tool calling, intent routing, and session memory — all running locally via Streamlit.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Streamlit UI                       │
│  (Sidebar · Applicant Snapshot · Chat Interface)     │
└──────────────────────┬──────────────────────────────┘
                       │ user query
                       ▼
┌──────────────────────────────────────────────────────┐
│               LLM-Based Router                        │
│  Classifies intent → ELIGIBILITY | PRODUCT_MATCH     │
│                       EMI_CALC   | GENERAL            │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│            LangChain Tool-Calling Agent               │
│  • System prompt with advisor persona                │
│  • 5 registered tools with schemas                   │
│  • Session memory (RunnableWithMessageHistory)       │
└──────────┬────────┬────────┬────────┬────────┬───────┘
           │        │        │        │        │
           ▼        ▼        ▼        ▼        ▼
      check_    get_loan  calculate  assess   get_
      eligib    products  _emi       _risk    applicant
      ility                          profile  _summary
           │        │        │        │        │
           └────────┴────────┴────────┴────────┘
                            │
                     CSV Dataset
            (creditsage_loan_applications.csv)
```

---

## 📁 Project Structure

```
solution_template/
├── run.py                  # Entry point — python run.py
├── start.py                # Alias entry point
├── app.py                  # Streamlit UI
├── agent/
│   ├── __init__.py
│   ├── agent.py            # LangChain tool-calling agent
│   ├── router.py           # LLM-based intent classifier
│   └── memory.py           # Session memory management
├── tools/
│   ├── __init__.py
│   ├── eligibility.py      # check_eligibility()
│   ├── loan_products.py    # get_loan_products()
│   ├── emi_calculator.py   # calculate_emi()
│   ├── risk_profile.py     # assess_risk_profile()
│   └── applicant_summary.py# get_applicant_summary()
├── data/
│   └── creditsage_loan_applications.csv
├── .env.example            # Environment variable template
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## 🚀 Setup & Run

### 1. Clone & Navigate
```bash
cd solution_template
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key:
#   OPENAI_API_KEY=sk-...
#   MODEL_NAME=gpt-4o-mini
```

### 4. Place Dataset
Ensure `creditsage_loan_applications.csv` is in the `data/` directory (a sample is included).

### 5. Launch
```bash
python run.py
# OR
streamlit run app.py
```

The app will open at **http://localhost:8501**.

---

## 🔑 Environment Variables

| Variable | Description | Required |
|---|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key | ✅ |
| `MODEL_NAME` | Model to use (default: `gpt-4o-mini`) | Optional |
| `LLM_PROVIDER` | Provider name: `openai` | Optional |

---

## 🛠️ Tools

| Tool | Parameters | Description |
|---|---|---|
| `check_eligibility` | `applicant_id` | Checks age, credit score, income against loan-type thresholds |
| `get_loan_products` | `loan_purpose`, `requested_amount` | Returns up to 3 matching products sorted by rate |
| `calculate_emi` | `principal`, `annual_rate`, `tenure_months` | Reducing-balance EMI formula |
| `assess_risk_profile` | `applicant_id` | 4-factor risk scoring (0–100) → Low/Medium/High |
| `get_applicant_summary` | `applicant_id` | Full applicant profile from CSV |

---

## 🧠 Router Pattern

The router uses **LLM-based intent classification** (not keyword matching). Each query is sent to the LLM with a structured classification prompt that returns one of:

- **ELIGIBILITY** → `check_eligibility()` + `assess_risk_profile()`
- **PRODUCT_MATCH** → `get_loan_products()` + `check_eligibility()`
- **EMI_CALC** → `calculate_emi()` (supports multi-scenario)
- **GENERAL** → LLM answer from knowledge + context

---

## 💬 Example Queries

- *"Am I eligible for a home loan?"*
- *"What loan products are available for me?"*
- *"Calculate EMI for ₹10 lakh at 10% for 5 years"*
- *"Compare 3-year vs 5-year tenure for my loan"*
- *"What documents do I need for a personal loan?"*
